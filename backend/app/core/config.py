from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "CopytradeBinance"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://copytrade:copytrade_dev_password@db:5432/copytrade"
    )

    jwt_secret: str = "dev-only-change-me"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7
    admin_email: str = "admin@example.com"
    admin_initial_password: str = "Admin123!ChangeMe"

    cors_origins: str = "http://localhost:8080,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
