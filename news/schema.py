"""Create missing application tables at startup without running migrations."""

from django.db import connection

from .models import Notification, Publication, Source


def ensure_schema():
    existing_tables = set(connection.introspection.table_names())
    with connection.schema_editor() as editor:
        for model in (Source, Publication, Notification):
            if model._meta.db_table not in existing_tables:
                editor.create_model(model)
                existing_tables.add(model._meta.db_table)
