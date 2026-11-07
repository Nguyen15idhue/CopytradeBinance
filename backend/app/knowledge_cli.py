"""CLI index code/docs cho agent: python -m app.knowledge_cli index [--dry-run]."""

import argparse
import asyncio
import json
from pathlib import Path

from app.core.database import SessionLocal
from app.services.agent.knowledge import count_chunks, index_files


async def cmd_index(dry_run: bool) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    async with SessionLocal() as db:
        stats = await index_files(db, repo_root, dry_run=dry_run)
    if not dry_run:
        async with SessionLocal() as db:
            stats["stored"] = await count_chunks(db)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Index code/docs cho agent")
    parser.add_argument("command", choices=["index"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "index":
        return asyncio.run(cmd_index(args.dry_run))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
