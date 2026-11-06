import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.performance import PerformanceMetric
from app.models.snapshot import PortfolioSnapshot
from app.models.trader import Trader
from app.models.universe import TraderUniverse
from app.models.user import User
from app.services.collector.demo import EXCLUDED_ID, QUALIFIED_ID, DemoAdapter

settings = get_settings()
WINDOWS = ("7D", "30D", "90D", "180D")


def _decimal(value):
    if value is None:
        return None
    return Decimal(str(value))


async def seed_user(email: str, password: str, role: str) -> None:
    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"Tài khoản đã tồn tại: {email}")
            return
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
            )
        )
        await db.commit()
        print(f"Đã tạo {role}: {email}")


async def seed_admin() -> None:
    await seed_user(settings.admin_email, settings.admin_initial_password, "admin")


async def seed_viewer() -> None:
    await seed_user("viewer@example.com", "Viewer123!ChangeMe", "viewer")


async def seed_traders() -> None:
    adapter = DemoAdapter()
    now = datetime.now(UTC)
    fixtures = [
        (EXCLUDED_ID, "excluded", ["runtime_lt_30", "aum_lt_5000"], Decimal("0")),
        (QUALIFIED_ID, "qualified", [], Decimal("82.6328")),
    ]
    async with SessionLocal() as db:
        for portfolio_id, tier, reasons, pre_score in fixtures:
            detail = await adapter.get_detail(portfolio_id)
            runtime_days = float(detail["runtimeDays"])
            trader = await db.get(Trader, portfolio_id)
            if trader is None:
                trader = Trader(lead_portfolio_id=portfolio_id)
                db.add(trader)
            trader.nickname = detail["nickname"]
            trader.portfolio_type = detail["portfolioType"]
            trader.status = detail["status"]
            trader.description = detail["description"]
            trader.start_time = now - timedelta(days=runtime_days)
            trader.last_trade_time = now
            trader.init_invest_asset = "USDT"

            universe = await db.get(TraderUniverse, portfolio_id)
            if universe is None:
                universe = TraderUniverse(lead_portfolio_id=portfolio_id)
                db.add(universe)
            universe.potential_tier = tier
            universe.pre_score = pre_score
            universe.filter_reasons = reasons
            universe.deep_fetch_status = "skipped" if tier == "excluded" else "done"

            snapshot_exists = await db.execute(
                select(PortfolioSnapshot.id)
                .where(
                    PortfolioSnapshot.lead_portfolio_id == portfolio_id,
                    PortfolioSnapshot.source == "demo",
                )
                .limit(1)
            )
            if snapshot_exists.scalar_one_or_none() is None:
                db.add(
                    PortfolioSnapshot(
                        lead_portfolio_id=portfolio_id,
                        collected_at=now,
                        collected_hour=now.replace(minute=0, second=0, microsecond=0),
                        source="demo",
                        raw={**detail, "collectedAt": now.isoformat()},
                        schema_version=1,
                    )
                )

            for window in WINDOWS:
                metric_exists = await db.execute(
                    select(PerformanceMetric.id)
                    .where(
                        PerformanceMetric.lead_portfolio_id == portfolio_id,
                        PerformanceMetric.time_range == window,
                    )
                    .limit(1)
                )
                if metric_exists.scalar_one_or_none() is not None:
                    continue
                data = await adapter.get_performance(portfolio_id, window)
                db.add(
                    PerformanceMetric(
                        lead_portfolio_id=portfolio_id,
                        time_range=window,
                        collected_at=now,
                        roi=_decimal(data["roi"]),
                        pnl=_decimal(data["pnl"]),
                        mdd=_decimal(data["mdd"]),
                        copier_pnl=_decimal(data["copierPnl"]),
                        win_rate=_decimal(data["winRate"]),
                        win_orders=data["winOrders"],
                        total_orders=data["totalOrder"],
                        sharpe=_decimal(data["sharpRatio"]),
                        raw=data,
                    )
                )
        await db.commit()
        print("Đã seed 2 trader: excluded + qualified")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dữ liệu Phase 1")
    parser.add_argument(
        "target",
        choices=["admin", "viewer", "traders", "all"],
        nargs="?",
        default="all",
    )
    args = parser.parse_args()
    if args.target in ("admin", "all"):
        await seed_admin()
    if args.target in ("viewer", "all"):
        await seed_viewer()
    if args.target in ("traders", "all"):
        await seed_traders()


if __name__ == "__main__":
    asyncio.run(main())
