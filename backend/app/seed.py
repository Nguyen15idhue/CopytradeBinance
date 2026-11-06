import argparse
import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User

settings = get_settings()


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


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed tài khoản Phase 1")
    parser.add_argument("target", choices=["admin", "viewer", "all"], nargs="?", default="admin")
    args = parser.parse_args()
    if args.target in ("admin", "all"):
        await seed_admin()
    if args.target in ("viewer", "all"):
        await seed_viewer()


if __name__ == "__main__":
    asyncio.run(main())
