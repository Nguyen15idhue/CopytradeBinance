"""Tool DB cho agent: search/profile/compare/ranking/risk/health-detail.

Không cho LLM tự viết SQL ở bước này; filter có cấu trúc, limit tối đa 50.
"""

from typing import Any

from sqlalchemy import and_, asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ranking_snapshot import RankingSnapshot
from app.models.risk_event import RiskEvent
from app.models.scoring_config import ScoringConfig
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.models.trader_metric import TraderMetric
from app.models.trader_score import TraderScore
from app.models.universe import TraderUniverse
from app.services.agent.schema import EvidenceItem, ToolResult, utcnow_iso
from app.services.agent.tools import register_tool
from app.services.compare import build_compare
from app.services.screener import SORT_COLUMNS, ScreenerFilters, apply_filters, base_statement

SAFE_SORT = dict(SORT_COLUMNS)
SAFE_SORT["risk_score"] = TraderMetric.risk_score


def _float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _ev(
    trader_id: str, label: str, value: Any, unit: str | None, as_of: str | None
) -> EvidenceItem:
    return EvidenceItem(
        id=f"{trader_id}:{label}", label=label, value=value, unit=unit,
        source="database", as_of=as_of, row_id=trader_id,
    )


@register_tool(
    "search_traders",
    "Tìm trader theo filter có cấu trúc (tier/risk/score/MDD/Sharpe/slot).",
    {
        "type": "object",
        "properties": {
            "tier": {"type": "array", "items": {"type": "string"}},
            "risk_level": {"type": "array", "items": {"type": "string"}},
            "risk_score_max": {"type": "number"},
            "low_risk_eligible": {"type": "boolean"},
            "no_veto": {"type": "boolean"},
            "min_runtime_days": {"type": "number"},
            "max_mdd_90d": {"type": "number"},
            "max_leverage": {"type": "number"},
            "min_sharpe": {"type": "number"},
            "min_confidence": {"type": "number"},
            "min_score": {"type": "number"},
            "has_slot": {"type": "boolean"},
            "sort": {"type": "array"},
            "limit": {"type": "integer"},
        },
    },
)
async def search_traders(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    limit = max(1, min(int(args.get("limit") or 10), 50))
    filters = ScreenerFilters(
        potential_tier=list(args.get("tier") or []),
        risk_level=list(args.get("risk_level") or []),
        min_runtime_days=args.get("min_runtime_days"),
        max_mdd_90d=args.get("max_mdd_90d"),
        max_leverage=args.get("max_leverage"),
        min_sharpe=args.get("min_sharpe"),
    )
    version_row = (
        await db.execute(select(ScoringConfig).where(ScoringConfig.is_active.is_(True)))
    ).scalars().first()
    version = version_row.version if version_row else 1
    statement = apply_filters(base_statement(version), filters)
    if args.get("risk_score_max") is not None:
        statement = statement.where(TraderMetric.risk_score <= float(args["risk_score_max"]))
    if args.get("no_veto"):
        statement = statement.where(
            or_(TraderMetric.risk_veto.is_(None), TraderMetric.risk_veto == [])
        )
    if args.get("min_score") is not None:
        statement = statement.where(TraderScore.score >= float(args["min_score"]))
    if args.get("min_confidence") is not None:
        statement = statement.where(TraderScore.confidence >= float(args["min_confidence"]))
    sorts = args.get("sort") or [{"field": "score", "dir": "desc"}]
    order_clauses = []
    for item in sorts[:2]:
        column = SAFE_SORT.get(item.get("field", "score"), TraderScore.score)
        direction = asc if item.get("dir") == "asc" else desc
        order_clauses.append(direction(column).nulls_last())
    order_clauses.append(TraderMetric.lead_portfolio_id)
    rows = (
        await db.execute(statement.order_by(*order_clauses).limit(limit * 2))
    ).all()

    items: list[dict[str, Any]] = []
    for row in rows:
        universe, nickname, _ptype, _status, metric, score = row
        tid = universe.lead_portfolio_id
        if args.get("has_slot") and not await _has_slot(db, tid):
            continue
        as_of = metric.computed_at.isoformat() if metric and metric.computed_at else None
        items.append(
            {
                "id": tid,
                "nickname": nickname,
                "tier": universe.potential_tier,
                "score": _float(score.score) if score else None,
                "band": score.band if score else None,
                "confidence": _float(score.confidence) if score else None,
                "risk_level": metric.risk_level if metric else None,
                "risk_score": _float(metric.risk_score) if metric else None,
                "veto": metric.risk_veto if metric else None,
                "roi_90d": _float(metric.roi_90d) if metric else None,
                "mdd_90d": _float(metric.mdd_90d) if metric else None,
                "sharpe": _float(metric.sharpe_90d) if metric else None,
                "max_leverage": _float(metric.max_leverage) if metric else None,
                "runtime_days": _float(metric.runtime_days) if metric else None,
                "as_of": as_of,
            }
        )
        if len(items) >= limit:
            break
    evidence: list[EvidenceItem] = []
    for item in items:
        as_of = item.get("as_of")
        for label, unit in (("score", None), ("roi_90d", "%"), ("mdd_90d", "%"),
                            ("sharpe", None), ("risk_score", None)):
            if item.get(label) is not None:
                evidence.append(_ev(item["id"], label, item[label], unit, as_of))
    return ToolResult(
        data={"items": items, "total": len(items), "config_version": version},
        meta={"source": "database", "as_of": utcnow_iso(),
              "row_ids": [item["id"] for item in items], "config_version": version},
        evidence=evidence,
    )


async def _has_slot(db: AsyncSession, trader_id: str) -> bool:
    snap = (
        await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.lead_portfolio_id == trader_id,
                   PortfolioSnapshot.source == "detail")
            .order_by(PortfolioSnapshot.collected_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if snap is None or not snap.raw:
        return False
    raw = snap.raw if isinstance(snap.raw, dict) else {}
    current = raw.get("currentCopyCount")
    maximum = raw.get("maxCopyCount")
    if current is None or maximum is None:
        return False
    try:
        return int(current) < int(maximum)
    except (TypeError, ValueError):
        return False


@register_tool(
    "get_trader_profile",
    "Hồ sơ đầy đủ một trader: tier, metrics, score, risk, performance 4 window.",
    {"type": "object", "properties": {"trader_id": {"type": "string"}},
     "required": ["trader_id"]},
)
async def get_trader_profile(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    trader_id = str(args.get("trader_id") or "")
    if not trader_id:
        return ToolResult.fail("Thiếu trader_id")
    trader = await db.get(Trader, trader_id)
    universe = (
        await db.execute(
            select(TraderUniverse).where(TraderUniverse.lead_portfolio_id == trader_id)
        )
    ).scalars().first()
    metric = (
        await db.execute(
            select(TraderMetric).where(TraderMetric.lead_portfolio_id == trader_id)
        )
    ).scalars().first()
    score = (
        await db.execute(
            select(TraderScore, ScoringConfig.version)
            .join(ScoringConfig, ScoringConfig.version == TraderScore.config_version)
            .where(TraderScore.lead_portfolio_id == trader_id,
                   ScoringConfig.is_active.is_(True))
        )
    ).first()
    if trader is None and universe is None and metric is None:
        return ToolResult.fail(f"Không tìm thấy trader {trader_id}")
    metrics_blob = (metric.metrics if metric else None) or {}
    published = metrics_blob.get("published") or {}
    score_row, _version = score if score else (None, None)
    events = (
        await db.execute(
            select(RiskEvent)
            .where(RiskEvent.lead_portfolio_id == trader_id)
            .order_by(RiskEvent.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    as_of = metric.computed_at.isoformat() if metric and metric.computed_at else None
    profile = {
        "id": trader_id,
        "nickname": trader.nickname if trader else None,
        "tier": universe.potential_tier if universe else None,
        "reasons": universe.filter_reasons if universe else [],
        "score": _float(score_row.score) if score_row else None,
        "band": score_row.band if score_row else None,
        "breakdown": score_row.breakdown if score_row else {},
        "hard_flags": score_row.hard_flags if score_row else [],
        "confidence": _float(score_row.confidence) if score_row else None,
        "risk_level": metric.risk_level if metric else None,
        "risk_score": _float(metric.risk_score) if metric else None,
        "veto": metric.risk_veto if metric else None,
        "roi_90d": _float(metric.roi_90d) if metric else None,
        "mdd_90d": _float(metric.mdd_90d) if metric else None,
        "sharpe": _float(metric.sharpe_90d) if metric else None,
        "performance": {
            window: {"roi": (published.get(window) or {}).get("roi"),
                     "mdd": (published.get(window) or {}).get("mdd"),
                     "sharpe": (published.get(window) or {}).get("sharpe")}
            for window in ("7D", "30D", "90D", "180D")
        },
        "risk_events": [
            {"code": e.code, "severity": e.severity, "label": e.label, "evidence": e.evidence}
            for e in events
        ],
        "has_slot": await _has_slot(db, trader_id),
        "as_of": as_of,
    }
    evidence = [
        _ev(trader_id, "score", profile["score"], None, as_of),
        _ev(trader_id, "roi_90d", profile["roi_90d"], "%", as_of),
        _ev(trader_id, "mdd_90d", profile["mdd_90d"], "%", as_of),
        _ev(trader_id, "sharpe", profile["sharpe"], None, as_of),
        _ev(trader_id, "risk_score", profile["risk_score"], None, as_of),
    ]
    evidence = [item for item in evidence if item.value is not None]
    return ToolResult(
        data=profile,
        meta={"source": "database", "as_of": as_of or utcnow_iso(), "row_ids": [trader_id]},
        evidence=evidence,
    )


@register_tool(
    "compare_traders",
    "So sánh 2–4 trader: metrics, series, correlation estimated.",
    {"type": "object", "properties": {"trader_ids": {"type": "array", "items": {"type": "string"}}},
     "required": ["trader_ids"]},
)
async def compare_traders(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    ids = [str(item) for item in (args.get("trader_ids") or [])][:4]
    if len(ids) < 2:
        return ToolResult.fail("Cần 2–4 trader để so sánh")
    try:
        result = await build_compare(db, ids)
    except Exception as exc:  # noqa: BLE001
        return ToolResult.fail(f"compare lỗi: {exc}")
    evidence = []
    for item in result.get("items", []):
        tid = item.get("id")
        for label, unit in (("score", None), ("roi_90d", "%"), ("mdd_90d", "%"), ("sharpe", None)):
            if item.get(label) is not None:
                evidence.append(_ev(tid, label, item[label], unit, None))
    missing = result.get("missing") or []
    data = dict(result)
    data["warnings"] = [f"Thiếu dữ liệu: {mid}" for mid in missing] or None
    return ToolResult(
        data=data,
        meta={"source": "database", "as_of": utcnow_iso(), "row_ids": ids},
        evidence=evidence,
    )


@register_tool(
    "get_ranking",
    "Đọc snapshot ranking: overall/low_risk/consistency.",
    {"type": "object", "properties": {"board": {"type": "string"}, "top_n": {"type": "integer"}}},
)
async def get_ranking(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    board = str(args.get("board") or "overall")
    if board not in ("overall", "low_risk", "consistency"):
        return ToolResult.fail(f"Board không hợp lệ: {board}")
    top_n = max(1, min(int(args.get("top_n") or 10), 50))
    snap = (
        await db.execute(
            select(RankingSnapshot)
            .where(RankingSnapshot.board == board)
            .order_by(RankingSnapshot.collected_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if snap is None:
        return ToolResult.fail(f"Chưa có snapshot cho board {board}")
    rows = (snap.items if isinstance(snap.items, list) else [])[:top_n]
    as_of = snap.collected_at.isoformat() if snap.collected_at else None
    evidence = [
        _ev(str(item.get("id")), "score", item.get("score"), None, as_of)
        for item in rows if isinstance(item, dict) and item.get("score") is not None
    ]
    return ToolResult(
        data={"board": board, "items": rows,
              "config_version": snap.config_version, "snapshot_at": as_of},
        meta={"source": "database", "as_of": as_of or utcnow_iso(),
              "row_ids": [str(i.get("id")) for i in rows if isinstance(i, dict)],
              "config_version": snap.config_version},
        evidence=evidence,
    )


@register_tool(
    "get_risk_events",
    "Event risk theo trader hoặc toàn hệ thống.",
    {"type": "object", "properties": {"trader_id": {"type": "string"},
                                      "severity": {"type": "string"},
                                      "limit": {"type": "integer"}}},
)
async def get_risk_events(db: AsyncSession, args: dict[str, Any]) -> ToolResult:
    limit = max(1, min(int(args.get("limit") or 20), 50))
    statement = select(RiskEvent).order_by(RiskEvent.created_at.desc()).limit(limit)
    conditions = []
    if args.get("trader_id"):
        conditions.append(RiskEvent.lead_portfolio_id == str(args["trader_id"]))
    if args.get("severity"):
        conditions.append(RiskEvent.severity == str(args["severity"]))
    if conditions:
        statement = select(RiskEvent).where(and_(*conditions)).order_by(
            RiskEvent.created_at.desc()).limit(limit)
    rows = (await db.execute(statement)).scalars().all()
    items = [
        {"trader_id": e.lead_portfolio_id, "code": e.code, "severity": e.severity,
         "label": e.label, "evidence": e.evidence, "status": e.status,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in rows
    ]
    return ToolResult(
        data={"items": items, "total": len(items)},
        meta={"source": "database", "as_of": utcnow_iso(),
              "row_ids": [item["trader_id"] for item in items]},
        evidence=[],
    )
