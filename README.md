# Агрегатор новостей Telegram

Система для ручного сохранения публикаций из Telegram-каналов и просмотра общей ленты.
Лабораторные работы по дисциплине МиСПИСИТ.

Стек: Python 3.13, Django 5.2.18, Django Templates, HTML/CSS, PostgreSQL 17.11, Django ORM.

## Запуск

Репозиторий: [https://github.com/Kysarii/mispisit26](https://github.com/Kysarii/mispisit26)

Ветка: `lab3`

Pull Request: будет добавлен позже.

Образ: `kysarii/mispisit26:0.0.3`

Страница образа: [https://hub.docker.com/r/kysarii/mispisit26](https://hub.docker.com/r/kysarii/mispisit26)

Для запуска нужен Docker с поддержкой Docker Compose.

```sh
git clone -b lab3 https://github.com/Kysarii/mispisit26
cd mispisit26
docker compose up -d
```

После запуска сайт открывается по адресу [http://localhost:8000](http://localhost:8000).
Структура базы создаётся автоматически миграциями Django. При первом запуске с новым
томом лента пустая, демонстрационные записи не загружаются.

## Страницы

| Адрес | Что на странице |
| --- | --- |
| [http://localhost:8000/](http://localhost:8000/) | Главная, версия приложения, последние новости и переходы к действиям |
| [http://localhost:8000/news/](http://localhost:8000/news/) | Лента новостей и поиск по заголовку, тексту и названию канала |
| [http://localhost:8000/news/new/](http://localhost:8000/news/new/) | Форма добавления новости: заголовок, название канала, ссылка на публикацию и текст |
| `http://localhost:8000/news/<id>/` | Карточка сохранённой новости: полный текст, канал, время добавления и ссылка на оригинал; вместо `<id>` указывается номер записи |
| [http://localhost:8000/action-error/](http://localhost:8000/action-error/) | Причина последнего отказа: кто, что пытался сделать и почему действие отклонено; при первом открытии — пример |

Данные хранятся в PostgreSQL (сервис `db`, том `dbdata`). После `docker compose down`
и `docker compose up -d` записи сохраняются. Флаг `-v` у команды `docker compose down`
удаляет том вместе со всеми данными базы.
