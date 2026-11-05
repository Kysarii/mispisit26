from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .forms import NewsForm
from .storage import DuplicateNewsError, StorageError, create_news, get_news, list_news


def _render_error(request, *, action, reasons, status=400, is_demo=False):
    return render(
        request,
        "news/action_error.html",
        {
            "actor": "Пользователь",
            "action": action,
            "reasons": reasons,
            "error_status": status,
            "is_demo": is_demo,
        },
        status=200 if is_demo else status,
    )


def _storage_error(request):
    return _render_error(
        request,
        action="открыть или сохранить новости",
        reasons=[
            "Хранилище новостей временно недоступно. Действие не выполнено. "
            "Попробуйте позже или обратитесь к администратору."
        ],
        status=503,
    )


@require_GET
def home(request):
    try:
        items = list_news()
    except StorageError:
        return _storage_error(request)
    return render(
        request,
        "news/home.html",
        {"latest_news": items[:3], "news_count": len(items),
         "channel_count": len({item.source_id for item in items})},
    )


@require_GET
def news_list(request):
    query = request.GET.get("q", "").strip()[:120]
    try:
        items = list_news()
        total = len(items)
        if query:
            items = list_news(query)
    except StorageError:
        return _storage_error(request)
    return render(request, "news/news_list.html", {"news_items": items, "query": query, "total": total})


@require_http_methods(["GET", "POST"])
def news_create(request):
    form = NewsForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        reasons = []
        if form.is_valid():
            try:
                item = create_news(form.cleaned_data)
            except DuplicateNewsError as exc:
                reasons = [str(exc)]
            except StorageError:
                return _storage_error(request)
            else:
                request.session.pop("action_error", None)
                response = HttpResponseRedirect(
                    reverse("news:detail", args=[item.pk]) + "?created=1"
                )
                response.status_code = 303
                return response
        else:
            reasons = [
                f"{form[field].label}: {message}"
                for field, messages in form.errors.items() for message in messages
            ]
        # Only short validation messages enter the signed cookie, never the news text.
        request.session["action_error"] = {"reasons": reasons}
        response = HttpResponseRedirect(reverse("news:error"))
        response.status_code = 303
        return response
    return render(request, "news/news_form.html", {"form": form})


@require_GET
def news_detail(request, news_id):
    try:
        item = get_news(news_id)
    except StorageError:
        return _storage_error(request)
    if item is None:
        return _render_error(
            request,
            action=f"открыть новость №{news_id}",
            reasons=["Новость с таким номером не найдена. Проверьте адрес или вернитесь в ленту."],
            status=404,
        )
    return render(request, "news/news_detail.html", {"item": item, "created": request.GET.get("created") == "1"})


@require_GET
def action_error(request):
    error = request.session.get("action_error")
    is_demo = request.GET.get("demo") == "1" or error is None
    reasons = (
        ["Ссылка ведёт на другой сайт. Нужна публичная публикация Telegram вида https://t.me/channel/123."]
        if is_demo else error["reasons"]
    )
    return _render_error(request, action="добавить новость в ленту", reasons=reasons, is_demo=is_demo)


def page_not_found(request, exception):
    return _render_error(
        request,
        action="открыть страницу",
        reasons=["Такой страницы нет. Воспользуйтесь меню, чтобы продолжить."],
        status=404,
    )


def csrf_failure(request, reason=""):
    return _render_error(
        request,
        action="отправить форму добавления новости",
        reasons=["Не удалось проверить отправку формы. Откройте форму заново и повторите попытку."],
        status=403,
    )
