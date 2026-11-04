import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import Client, SimpleTestCase, override_settings

from .storage import create_news, list_news


class NewsFlowTests(SimpleTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data_file = Path(directory.name) / "news.json"
        settings_override = override_settings(NEWS_DATA_FILE=self.data_file)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.payload = {
            "title": "Новая публикация",
            "channel_name": "Учебный канал",
            "source_url": "https://t.me/channel/321",
            "body": "Первый абзац.\n\nВторой абзац.",
        }

    def test_five_pages_open_directly_with_shared_navigation(self):
        for url in ("/", "/news/", "/news/new/", "/news/1/", "/action-error/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Агрегатор новостей")
                for target in ("/", "/news/", "/news/new/", "/action-error/?demo=1"):
                    self.assertContains(response, f'href="{target}"')

    def test_create_persists_and_redirects_to_detail(self):
        response = self.client.post("/news/new/", self.payload)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, "/news/4/?created=1")
        item = json.loads(self.data_file.read_text(encoding="utf-8"))[-1]
        self.assertEqual(item["title"], self.payload["title"])
        self.assertEqual(item["body"], self.payload["body"])
        self.assertFalse(item["is_demo"])
        response = self.client.get(response.url)
        self.assertContains(response, "Новость сохранена.")
        self.assertContains(response, "<p>Первый абзац.</p>", html=True)
        self.assertContains(response, 'rel="noopener noreferrer"')

    def test_saved_news_is_visible_to_another_browser(self):
        self.client.post("/news/new/", self.payload)
        self.assertContains(Client().get("/news/"), self.payload["title"])
        self.assertEqual(list_news()[0]["id"], 4)

    def test_empty_form_redirects_to_real_error_without_creating_news(self):
        response = self.client.post("/news/new/", {}, follow=True)
        self.assertEqual(response.redirect_chain, [("/action-error/", 303)])
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Пользователь демоверсии", status_code=400)
        self.assertContains(response, "Укажите заголовок новости.", status_code=400)
        self.assertContains(response, "Добавьте текст новости.", status_code=400)
        self.assertFalse(response.context["is_demo"])
        self.assertEqual(len(list_news()), 3)

    def test_invalid_telegram_links_are_rejected(self):
        for source_url in (
            "https://example.com/channel/321",
            "https://t.me/channel",
            "https://t.me/channel/0",
            "https://t.me.evil.example/channel/321",
            "https://t.me@evil.example/channel/321",
            "http://t.me/channel/321",
            "javascript:alert(1)",
            "https://t.me/+invite",
        ):
            with self.subTest(source_url=source_url):
                response = self.client.post(
                    "/news/new/", {**self.payload, "source_url": source_url}, follow=True
                )
                self.assertEqual(response.status_code, 400)
        self.assertEqual(len(list_news()), 3)

    def test_whitespace_and_overlong_fields_are_rejected(self):
        for update in ({"title": "   "}, {"title": "а" * 161}, {"body": "б" * 10001}):
            with self.subTest(field=next(iter(update))):
                response = self.client.post("/news/new/", {**self.payload, **update}, follow=True)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(len(list_news()), 3)

    def test_duplicate_normalized_url_is_rejected(self):
        self.client.post("/news/new/", self.payload)
        response = self.client.post(
            "/news/new/",
            {**self.payload, "source_url": "https://t.me/CHANNEL/321/?single"},
            follow=True,
        )
        self.assertContains(response, "Новость с этой ссылкой уже есть в ленте.", status_code=400)
        self.assertEqual(len(list_news()), 4)

    def test_error_is_scoped_to_the_browser_and_demo_is_always_available(self):
        self.client.post("/news/new/", {})
        self.assertEqual(self.client.get("/action-error/").status_code, 400)
        self.assertTrue(Client().get("/action-error/").context["is_demo"])
        self.assertTrue(self.client.get("/action-error/?demo=1").context["is_demo"])
        self.client.post("/news/new/", self.payload)
        self.assertTrue(self.client.get("/action-error/").context["is_demo"])

    def test_error_cookie_does_not_contain_the_news_text(self):
        self.client.post("/news/new/", {**self.payload, "source_url": "https://example.com"})
        self.assertEqual(list(self.client.session.keys()), ["action_error"])
        self.assertNotIn(self.payload["body"], str(dict(self.client.session)))

    def test_search_is_case_insensitive_and_can_find_channel_or_text(self):
        self.client.post("/news/new/", self.payload)
        for query in ("НОВАЯ ПУБЛИКАЦИЯ", "учебный канал", "ВТОРОЙ АБЗАЦ"):
            with self.subTest(query=query):
                response = self.client.get("/news/", {"q": query})
                self.assertEqual(len(response.context["news_items"]), 1)
                self.assertContains(response, self.payload["title"])
        self.assertContains(self.client.get("/news/", {"q": "Несуществующая строка"}), "Ничего не найдено")

    def test_empty_storage_stays_empty_and_offers_creation(self):
        self.data_file.write_text("[]", encoding="utf-8")
        self.assertContains(self.client.get("/news/"), "В ленте пока тихо")
        self.assertEqual(list_news(), [])
        self.assertEqual(self.client.get("/").status_code, 200)
        response = self.client.post("/news/new/", self.payload)
        self.assertEqual(response.url, "/news/1/?created=1")

    def test_unknown_news_and_unknown_route_use_navigable_error_template(self):
        for url in ("/news/99999/", "/missing-page/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, "news/action_error.html")
                self.assertContains(response, 'href="/news/"', status_code=404)

    def test_user_content_is_escaped_in_list_detail_and_search(self):
        payload = {**self.payload, "title": '<script>alert("xss")</script>', "body": "<img src=x onerror=alert(1)>"}
        self.client.post("/news/new/", payload)
        for url in ("/news/", "/news/4/"):
            response = self.client.get(url)
            self.assertContains(response, "&lt;script&gt;")
            self.assertNotContains(response, "<script>")
            self.assertNotContains(response, "<img src=x")
        self.assertNotContains(self.client.get("/news/", {"q": payload["title"]}), "<script>")

    def test_csrf_is_required_and_the_refusal_has_navigation(self):
        browser = Client(enforce_csrf_checks=True)
        denied = browser.post("/news/new/", self.payload)
        self.assertContains(denied, "Не удалось проверить отправку формы.", status_code=403)
        self.assertContains(denied, 'href="/news/"', status_code=403)
        browser.get("/news/new/")
        accepted = browser.post(
            "/news/new/", {**self.payload, "csrfmiddlewaretoken": browser.cookies["csrftoken"].value}
        )
        self.assertEqual(accepted.status_code, 303)

    def test_corrupt_storage_is_reported_without_overwriting_it(self):
        for content in ("broken json", "{}", '[{"id": 1}]'):
            with self.subTest(content=content):
                self.data_file.write_text(content, encoding="utf-8")
                self.assertEqual(self.client.get("/news/").status_code, 503)
                self.assertEqual(self.client.post("/news/new/", self.payload).status_code, 503)
                self.assertEqual(self.data_file.read_text(encoding="utf-8"), content)

    def test_failed_write_keeps_existing_records(self):
        list_news()
        original = self.data_file.read_text(encoding="utf-8")
        with patch("news.storage.os.replace", side_effect=OSError("disk unavailable")):
            response = self.client.post("/news/new/", self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.data_file.read_text(encoding="utf-8"), original)
        self.assertEqual(list(self.data_file.parent.glob("*.tmp")), [])

    def test_parallel_submissions_do_not_lose_records(self):
        list_news()
        def save(index):
            return create_news({**self.payload, "source_url": f"https://t.me/channel/{400 + index}"})
        with ThreadPoolExecutor(max_workers=4) as executor:
            ids = [item["id"] for item in executor.map(save, range(8))]
        self.assertEqual(len(set(ids)), 8)
        self.assertEqual(len(list_news()), 11)

    def test_creation_does_not_accept_get_query_data(self):
        self.client.get("/news/new/", self.payload)
        self.assertEqual(len(list_news()), 3)
        self.assertEqual(self.client.put("/news/new/").status_code, 405)
