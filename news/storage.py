"""Read and save news through the Django ORM in PostgreSQL."""

from urllib.parse import urlsplit

from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q

from .models import Publication, Source


class StorageError(Exception):
    pass


class DuplicateNewsError(Exception):
    pass


def list_news(query=""):
    try:
        items = Publication.objects.select_related("source")
        if query:
            items = items.filter(
                Q(title__icontains=query)
                | Q(content_text__icontains=query)
                | Q(source__title__icontains=query)
            )
        return list(items)
    except DatabaseError as exc:
        raise StorageError("Не удалось прочитать новости из базы данных.") from exc


def get_news(news_id):
    if news_id > 9223372036854775807:
        return None
    try:
        return Publication.objects.select_related("source").get(pk=news_id)
    except Publication.DoesNotExist:
        return None
    except DatabaseError as exc:
        raise StorageError("Не удалось прочитать новость из базы данных.") from exc


def create_news(data):
    username, post_id = urlsplit(data["source_url"]).path.strip("/").split("/")
    try:
        with transaction.atomic():
            source, _ = Source.objects.update_or_create(
                link=f"https://t.me/{username}",
                defaults={"title": data["channel_name"]},
            )
            return Publication.objects.create(
                source=source,
                external_id=int(post_id),
                title=data["title"],
                content_text=data["body"],
            )
    except IntegrityError as exc:
        constraint = getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None)
        if constraint == "unique_source_external_id":
            raise DuplicateNewsError("Публикация с этой ссылкой уже есть в базе.") from exc
        raise StorageError("Не удалось сохранить новость в базе данных.") from exc
    except DatabaseError as exc:
        raise StorageError("Не удалось сохранить новость в базе данных.") from exc
