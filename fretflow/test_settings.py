"""Run account tests on a separate PostgreSQL server/database, never SQLite."""

import os

import dj_database_url

from .settings import *  # noqa: F403

test_url = os.environ.get('TEST_DATABASE_URL')
if not test_url:
    raise ValueError('Set TEST_DATABASE_URL to a disposable PostgreSQL database first.')
DATABASES = {'default': dj_database_url.parse(test_url)}
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ValueError('Tests require PostgreSQL too.')
# Django creates and drops its own test database; its public schema is isolated
# from the hosted app's private fretflow schema and real member records.
