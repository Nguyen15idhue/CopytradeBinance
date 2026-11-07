"""Settings: đọc/ghi cấu hình, version hoá scoring, preview impact, audit."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models.audit_log import AuditLog
from app.models.scoring_config import ScoringConfig
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.services import scoring as sc
from app.services.config_store import get_setting, set_setting
from app.services.crypto import encrypt_secret
from app.services.scoring_service import _components, build_scores

AI_CONFIG_KEY = "ai.config"
COLLECTOR_CONFIG_KEY = "collector.config"


class ScoringUpdate(BaseModel):
    weights: dict[str, float] | None = None
    hard_filters: dict[str, Any] | None = None

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, value: dict[str, float] | None):
        if value is None:
            return value
        unknown = set(value) - set(sc.GROUP_WEIGHTS)
        if unknown:
            raise ValueError(f"nhóm trọng số lạ: {sorted(unknown)}")
        if any(weight < 0 or weight > 100 for weight in value.values()):
            raise ValueError("trọng số phải trong 0–100")
        if sum(value.values()) <= 0:
            raise ValueError("tổng trọng số phải > 0")
        return value


class AIUpdate(BaseModel):
    model_primary: str | None = Field(default=None, max_length=128)
    model_fallback: str | None = Field(default=None, max_length=128)
    monthly_budget_usd: float | None = Field(default=None, ge=0, le=10000)
    daily_budget_usd: float | None = Field(default=None, ge=0, le=10000)
    enabled: bool | None = None
    api_key: str | None = Field(default=None, max_length=256)


class CollectorUpdate(BaseModel):
    scan_interval_min: int | None = Field(default=None, ge=5, le=1440)
    deep_interval_hours_watch: int | None = Field(default=None, ge=1, le=168)
    deep_interval_hours_qualified: int | None = Field(default=None, ge=1, le=168)
    deep_interval_hours_high: int | None = Field(default=None, ge=1, le=168)


class SettingsUpdate(BaseModel):
    scoring: ScoringUpdate | None = None
    ai: AIUpdate | None = None
    collector: CollectorUpdate | None = None


def _masked(value: str | None) -> str:
    return "••••" if value else ""


async def active_config(db: AsyncSession) -> ScoringConfig:
    config = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    if config is None:
        config = ScoringConfig(
            version=1,
            weights=sc.GROUP_WEIGHTS,
            normalization={"method": "percentile_rank", "winsorize": [2.5, 97.5]},
            hard_filters={},
            is_active=True,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


async def get_ai_api_key(db: AsyncSession | None = None) -> str:
    """Env là nguồn chính; override mã hoá trong app_settings được thêm ở bước 5.3."""
    if db is not None:
        from app.services.crypto import decrypt_secret

        stored = await get_setting(db, "ai.openrouter_key")
        if stored:
            try:
                return decrypt_secret(stored)
            except Exception:  # noqa: BLE001 - key hỏng thì fallback env
                pass
    return get_settings().openrouter_api_key


async def get_ai_config(db: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    override = (await get_setting(db, AI_CONFIG_KEY)) or {}
    key = await get_ai_api_key(db)
    return {
        "model_primary": override.get("model_primary", settings.ai_model_primary),
        "model_fallback": override.get("model_fallback", settings.ai_model_fallback),
        "monthly_budget_usd": float(
            override.get("monthly_budget_usd", settings.ai_monthly_budget_usd)
        ),
        "daily_budget_usd": float(
            override.get("daily_budget_usd", settings.ai_daily_budget_usd)
        ),
        "enabled": bool(override.get("enabled", settings.ai_enabled)),
        "key_configured": bool(key),
        "key_masked": _masked(key),
    }


async def get_collector_config(db: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    override = (await get_setting(db, COLLECTOR_CONFIG_KEY)) or {}
    return {
        "scan_interval_min": int(override.get("scan_interval_min", settings.scan_interval_min)),
        "deep_interval_hours_watch": int(
            override.get("deep_interval_hours_watch", settings.deep_interval_hours_watch)
        ),
        "deep_interval_hours_qualified": int(
            override.get(
                "deep_interval_hours_qualified", settings.deep_interval_hours_qualified
            )
        ),
        "deep_interval_hours_high": int(
            override.get("deep_interval_hours_high", settings.deep_interval_hours_high)
        ),
    }


async def get_settings_snapshot(db: AsyncSession) -> dict[str, Any]:
    settings = get_settings()
    config = await active_config(db)
    return {
        "scoring": {
            "version": config.version,
            "weights": config.weights,
            "hard_filters": config.hard_filters,
            "normalization": config.normalization,
        },
        "ai": await get_ai_config(db),
        "collector": await get_collector_config(db),
        "system": {
            "app_env": settings.app_env,
            "app_name": settings.app_name,
            "api_v1_prefix": settings.api_v1_prefix,
        },
    }


async def _audit(
    db: AsyncSession,
    user_id: UUID | None,
    action: str,
    entity: str,
    entity_id: str | None,
    before: dict | None,
    after: dict | None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
        )
    )


async def list_versions(db: AsyncSession) -> list[ScoringConfig]:
    return (
        await db.execute(select(ScoringConfig).order_by(ScoringConfig.version.desc()))
    ).scalars().all()


async def update_settings(
    db: AsyncSession, payload: SettingsUpdate, user_id: UUID | None
) -> dict[str, Any]:
    changed: dict[str, Any] = {}
    if payload.scoring and (payload.scoring.weights or payload.scoring.hard_filters):
        current = await active_config(db)
        weights = payload.scoring.weights or current.weights
        hard_filters = payload.scoring.hard_filters or current.hard_filters
        if sum(weights.values()) <= 0:
            raise ApiError(422, "INVALID_WEIGHTS", "Tổng trọng số phải > 0")
        next_version = int(
            await db.scalar(select(func.max(ScoringConfig.version))) or 0
        ) + 1
        await db.execute(
            ScoringConfig.__table__.update().values(is_active=False)
        )
        config = ScoringConfig(
            version=next_version,
            weights=weights,
            normalization=current.normalization,
            hard_filters=hard_filters,
            is_active=True,
        )
        db.add(config)
        await _audit(
            db,
            user_id,
            "scoring.update",
            "scoring_config",
            str(next_version),
            {"version": current.version, "weights": current.weights},
            {"version": next_version, "weights": weights},
        )
        changed["scoring_version"] = next_version
        await db.commit()
        await build_scores(db)

    if payload.ai:
        data = payload.ai.model_dump(exclude_none=True)
        api_key = data.pop("api_key", None)
        if api_key:
            await set_setting(db, "ai.openrouter_key", encrypt_secret(api_key))
            await _audit(
                db, user_id, "ai.key_update", "app_settings", "ai.openrouter_key", None,
                {"configured": True},
            )
            changed["ai_key_configured"] = True
        if data:
            override = (await get_setting(db, AI_CONFIG_KEY)) or {}
            override.update(data)
            await set_setting(db, AI_CONFIG_KEY, override)
            await _audit(db, user_id, "ai.update", "app_settings", AI_CONFIG_KEY, None, override)
            changed["ai"] = override

    if payload.collector:
        override = (await get_setting(db, COLLECTOR_CONFIG_KEY)) or {}
        override.update(payload.collector.model_dump(exclude_none=True))
        await set_setting(db, COLLECTOR_CONFIG_KEY, override)
        await _audit(
            db,
            user_id,
            "collector.update",
            "app_settings",
            COLLECTOR_CONFIG_KEY,
            None,
            override,
        )
        changed["collector"] = override

    await db.commit()
    return await get_settings_snapshot(db)


async def preview_impact(
    db: AsyncSession, weights: dict[str, float], version: int | None = None
) -> dict[str, Any]:
    if not weights or sum(weights.values()) <= 0:
        raise ApiError(422, "INVALID_WEIGHTS", "Tổng trọng số phải > 0")
    rows = (
        await db.execute(
            select(TraderMetric, TraderScore)
            .join(
                TraderScore,
                TraderScore.lead_portfolio_id == TraderMetric.lead_portfolio_id,
            )
            .where(TraderScore.config_version == (version or 1))
        )
    ).all()
    prepared = [
        {
            "id": metric.lead_portfolio_id,
            "metrics": metric.metrics or {},
            "old_score": float(score.score) if score.score is not None else None,
            "old_band": score.band,
            "old_rankable": score.rankable,
        }
        for metric, score in rows
    ]
    for item in prepared:
        item["components"] = _components(item["metrics"])

    scored = sc.compute_scores(prepared)
    changes = []
    changed_band = 0
    for source, result in zip(prepared, scored, strict=True):
        if source["old_band"] != result["band"]:
            changed_band += 1
        changes.append(
            {
                "id": source["id"],
                "old_score": source["old_score"],
                "new_score": result["score"],
                "old_band": source["old_band"],
                "new_band": result["band"],
                "delta": round((result["score"] or 0) - (source["old_score"] or 0), 2),
            }
        )
    changes.sort(key=lambda item: abs(item["delta"]), reverse=True)
    return {
        "traders": len(prepared),
        "changed_band": changed_band,
        "top_changes": changes[:10],
        "weights": weights,
    }


async def rollback(db: AsyncSession, version: int, user_id: UUID | None) -> dict[str, Any]:
    target = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.version == version))
    ).scalars().first()
    if target is None:
        raise ApiError(404, "CONFIG_VERSION_NOT_FOUND", "Không tìm thấy version")
    current = await active_config(db)
    await db.execute(ScoringConfig.__table__.update().values(is_active=False))
    target.is_active = True
    await _audit(
        db,
        user_id,
        "scoring.rollback",
        "scoring_config",
        str(version),
        {"version": current.version},
        {"version": version},
    )
    await db.commit()
    await build_scores(db)
    return await get_settings_snapshot(db)
