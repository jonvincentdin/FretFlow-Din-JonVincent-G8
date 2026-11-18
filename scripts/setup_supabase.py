"""Apply the private-schema migration using the Supabase CLI, then Django."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
database_url = os.environ.get('DATABASE_URL', '')
if not database_url.startswith(('postgresql://', 'postgres://')):
    sys.exit('Set DATABASE_URL in .env to your Supabase PostgreSQL connection URI first.')

cli = shutil.which('supabase')
command = [cli] if cli else [
    shutil.which('npx.cmd' if os.name == 'nt' else 'npx') or 'npx',
    '--yes', 'supabase',
]
result = subprocess.run(
    command + ['db', 'push', f'--remote={database_url}', '--yes'],
    cwd=ROOT, capture_output=True, text=True,
)
# Keep credentials out of setup output, including CLI error messages.
password = urlsplit(database_url).password
output = (result.stdout + result.stderr).replace(database_url, '[database URL]')
if password:
    output = output.replace(password, '[password]').replace(unquote(password), '[password]')
print(output, end='', flush=True)
if result.returncode:
    sys.exit(result.returncode)
subprocess.run([sys.executable, 'manage.py', 'migrate'], cwd=ROOT, check=True)
