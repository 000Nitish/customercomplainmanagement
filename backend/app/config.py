from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db_utils import normalize_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""

    # Supabase PostgreSQL connection string (preferred for deployment)
    database_url: str = ""
    supabase_database_url: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    upload_dir: str = "./uploads"
    frontend_url: str = "http://localhost:5173"

    @property
    def sqlalchemy_database_url(self) -> str:
        configured = self.database_url or self.supabase_database_url
        if configured:
            return normalize_database_url(configured)
        return "sqlite:///./pharma_qms.db"

    @property
    def sqlalchemy_direct_url(self) -> str:
        return self.sqlalchemy_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
