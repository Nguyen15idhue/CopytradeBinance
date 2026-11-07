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

    cors_origins: str = "http://localhost:8090,http://localhost:5173"

    # Collector (Phase 2)
    bapi_base_url: str = "https://www.binance.com"
    bapi_concurrency: int = 6
    bapi_timeout_seconds: int = 20
    bapi_max_retries: int = 5
    redis_url: str = "redis://redis:6379/0"
    collector_kill_switch: bool = False
    aum_preset: int = 5000
    scan_interval_min: int = 60
    deep_interval_hours_watch: int = 6
    deep_interval_hours_qualified: int = 12
    deep_interval_hours_high: int = 24
    raw_archive_dir: str = "data/raw"

    # AI (Phase 5)
    ai_enabled: bool = True
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_model_primary: str = ""
    ai_model_fallback: str = ""
    ai_monthly_budget_usd: float = 20.0
    ai_daily_budget_usd: float = 2.0
    ai_timeout_seconds: int = 60
    ai_max_tokens: int = 2500
    ai_reasoning_effort: str = "auto"
    ai_cooldown_hours: int = 24
    prompt_version: str = "v1"

    # Ops (Phase 5)
    api_rate_limit_per_min: int = 100

    # Agent (Phase 6b)
    agent_enabled: bool = True
    agent_max_steps: int = 8
    agent_timeout_seconds: int = 120
    agent_rate_limit_per_min: int = 20
    agent_retention_days: int = 90
    tavily_api_key: str = ""
    agent_web_search_enabled: bool = True
    agent_web_search_max_results: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
