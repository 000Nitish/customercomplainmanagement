"""Database connection helpers for Supabase PostgreSQL."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def is_supabase_url(database_url: str) -> bool:
    host = urlparse(database_url).hostname or ""
    return "supabase.co" in host or "supabase.com" in host


def normalize_database_url(database_url: str) -> str:
    """Ensure psycopg2-compatible postgresql:// scheme."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def get_engine_connect_args(database_url: str) -> dict:
    """Supabase requires SSL for remote PostgreSQL connections."""
    if is_supabase_url(database_url):
        return {"sslmode": "require"}
    return {}


def get_engine_kwargs(database_url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True}
    connect_args = get_engine_connect_args(database_url)
    if connect_args:
        kwargs["connect_args"] = connect_args

    # Transaction pooler (port 6543) works best with smaller pools on serverless hosts.
    parsed = urlparse(database_url)
    if parsed.port == 6543:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 2

    return kwargs
