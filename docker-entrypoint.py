"""Apply the empty database schema before starting the application."""

import os
import sys

import django
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
call_command("migrate", interactive=False)
os.execvp(sys.argv[1], sys.argv[1:])
