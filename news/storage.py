"""JSON storage for the single-process teaching application; no database required."""

import json
import os
import tempfile
from pathlib import Path
from threading import RLock

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime


class StorageError(Exception):
    pass


class DuplicateNewsError(Exception):
    pass


_lock = RLock()
_seed_file = Path(__file__).parent / "fixtures" / "initial_news.json"


def _write(path, items):
    """Replace the file only after the complete new document has been written."""
    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(items, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _read():
    path = Path(settings.NEWS_DATA_FILE)
    try:
        if not path.exists():
            items = json.loads(_seed_file.read_text(encoding="utf-8"))
            _write(path, items)
        else:
            items = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(items, list):
            raise ValueError("Expected a list of news records")
        ids = set()
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ValueError("Invalid news record")
            if item["id"] < 1 or item["id"] in ids:
                raise ValueError("Invalid or duplicate news ID")
            ids.add(item["id"])
            for field in ("title", "channel_name", "source_url", "body", "created_at"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError("Missing news field")
            created_at = parse_datetime(item["created_at"])
            if created_at is None or timezone.is_naive(created_at):
                raise ValueError("Invalid news date")
        return items
    except (OSError, ValueError, TypeError) as exc:
        # Never silently replace damaged user data with the demo fixtures.
        raise StorageError("Не удалось прочитать хранилище новостей.") from exc


def list_news():
    with _lock:
        items = _read()
    return sorted(
        [{**item, "created_at": parse_datetime(item["created_at"])} for item in items],
        key=lambda item: (item["created_at"], item["id"]),
        reverse=True,
    )


def create_news(data):
    with _lock:
        items = _read()
        if any(item["source_url"] == data["source_url"] for item in items):
            raise DuplicateNewsError("Новость с этой ссылкой уже есть в ленте.")
        item = {
            "id": max((item["id"] for item in items), default=0) + 1,
            "title": data["title"],
            "channel_name": data["channel_name"],
            "source_url": data["source_url"],
            "body": data["body"],
            "created_at": timezone.now().isoformat(),
            "is_demo": False,
        }
        try:
            _write(Path(settings.NEWS_DATA_FILE), [*items, item])
        except OSError as exc:
            raise StorageError("Не удалось сохранить новость.") from exc
        return item
