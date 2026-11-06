from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "CopytradeBinance"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.jwt_access_ttl_min == 15
