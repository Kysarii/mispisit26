# Агрегатор новостей Telegram

Административная веб-панель для ручного сохранения публикаций из Telegram-каналов
и проверки записей в общей базе. Версия приложения: **0.0.5**.
Лабораторные работы по дисциплине МиСПИСИТ.

Стек: Python 3.13, Django 5.2.18, Django Templates, Bootstrap 5.3.8,
HTML/CSS, PostgreSQL 17.11, Django ORM.

## Запуск

Репозиторий: [https://github.com/Kysarii/mispisit26](https://github.com/Kysarii/mispisit26)

Ветка: `lab5`.

Pull Request: [https://github.com/Kysarii/mispisit26/pull/5](https://github.com/Kysarii/mispisit26/pull/5).

Образ: `kysarii/mispisit26:0.0.5`.


Страница образа: [https://hub.docker.com/r/kysarii/mispisit26](https://hub.docker.com/r/kysarii/mispisit26)

Для запуска нужен Docker с поддержкой Docker Compose.

```sh
git clone -b lab5 https://github.com/Kysarii/mispisit26
cd mispisit26
docker compose up -d
```

После запуска сайт открывается по адресу [http://localhost:8000](http://localhost:8000).
Порт 8000 сохранён из предыдущей работы. Структура базы создаётся автоматически
при запуске: `docker-entrypoint.py` вызывает `news.schema.ensure_schema`, а Django
`schema_editor` создаёт только отсутствующие таблицы моделей. Новые миграции не
добавляются, сохранённые записи не очищаются. Старый файл начальной миграции оставлен
как история предыдущих работ, при запуске он не выполняется. При первом запуске
с новым томом лента и уведомления пустые, демонстрационные записи не загружаются.

## Страницы

| Адрес | Что на странице |
| --- | --- |
| [http://localhost:8000/](http://localhost:8000/) | Главная административной панели, версия приложения, последние публикации и переходы к действиям |
| [http://localhost:8000/news/](http://localhost:8000/news/) | Список публикаций и поиск по заголовку, тексту и названию канала |
| [http://localhost:8000/news/new/](http://localhost:8000/news/new/) | Форма добавления новости: заголовок, название канала, ссылка на публикацию и текст |
| `http://localhost:8000/news/<id>/` | Карточка сохранённой новости: полный текст, канал, время добавления и ссылка на оригинал; вместо `<id>` указывается номер записи |
| [http://localhost:8000/notifications/](http://localhost:8000/notifications/) | Уведомления о добавленных публикациях: заголовок, канал, номер записи, время и статус «Новое / Прочитано» |
| [http://localhost:8000/action-error/](http://localhost:8000/action-error/) | Причина последнего отказа: кто, что пытался сделать и почему действие отклонено; при первом открытии — пример |

Данные хранятся в PostgreSQL (сервис `db`, том `dbdata`). После `docker compose down`
и `docker compose up -d` записи сохраняются. Флаг `-v` у команды `docker compose down`
удаляет том вместе со всеми данными базы.
