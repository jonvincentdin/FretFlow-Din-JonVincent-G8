-- Django owns app tables through manage.py migrate in this private schema.
-- Keep it out of the Supabase Data API's exposed schemas.
create schema if not exists fretflow;
revoke all on schema fretflow from public;
revoke all on schema fretflow from anon, authenticated;
