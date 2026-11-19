"""Create missing application tables before starting the application."""

import os
import sys

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from news.schema import ensure_schema

ensure_schema()
os.execvp(sys.argv[1], sys.argv[1:])
