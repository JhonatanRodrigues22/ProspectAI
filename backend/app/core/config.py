from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ProspectAI"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    google_places_api_key: str = ""
    google_places_base_url: str = "https://places.googleapis.com"
    viacep_base_url: str = "https://viacep.com.br"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
