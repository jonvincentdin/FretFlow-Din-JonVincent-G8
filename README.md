# FretFlow

A Django workspace for guitar practice and live performance.

The accounts app is the first delivery. Song libraries, chart tools and setlists
are tracked separately in [PROJECT_FLOW.md](PROJECT_FLOW.md).

## Run on Windows

Use Python 3.12 or newer and Node.js 22 or newer (for the Supabase CLI).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Skip copying the template when `.env` already contains your credentials.
Set `DJANGO_SECRET_KEY`, `DATABASE_URL` and `SUPABASE_URL` in `.env`.
Generate a signing key with:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Use the PostgreSQL **Session pooler** URI from Supabase's Connect panel, with
`?sslmode=require`. URL-encode special characters in its password. A Supabase
API key cannot replace this PostgreSQL connection. Name the Supabase project
**FretFlow**; its managed database normally keeps the name `postgres`.

```powershell
.\.venv\Scripts\python.exe scripts\setup_supabase.py
.\.venv\Scripts\python.exe manage.py runserver
```

Open <http://127.0.0.1:8000/>. The setup script invokes Supabase CLI v3 to
create the private `fretflow` schema, then runs Django migrations. Django owns
application-table migrations; do not add the private schema to the Data API's
exposed schemas. No SQLite database is used.

## Accounts

Public registration creates a Member and signs them in. Members can edit only
their own profile and preferences. Django staff accounts use a separate Admin
dashboard; entering another role's dashboard URL returns 403. Logout uses a
CSRF-protected POST.

Create the site's administrator privately:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

No default administrator or shared password is included.

## Checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Run the account suite against a **separate, disposable PostgreSQL instance**.
Its database user needs permission to create a test database. Django creates
and drops that test database; this command does not use the hosted app schema.

```powershell
$env:TEST_DATABASE_URL = 'postgresql://USER:PASSWORD@127.0.0.1:5432/postgres'
.\.venv\Scripts\python.exe manage.py test accounts --settings=fretflow.test_settings --noinput
```

The templates use a locally hosted Instrument Sans font. Its license is in
`static/accounts/fonts/OFL.txt`.

This is a local development setup with `DEBUG=True`. Production deployment and
its hosting/security configuration belong to the final project step.
