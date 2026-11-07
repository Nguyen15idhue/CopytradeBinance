"""Kiểm tra docs/ky-thuat khớp manifest của trang Tài liệu kỹ thuật."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "ky-thuat"
MANIFEST = ROOT / "frontend" / "src" / "content" / "technical" / "manifest.ts"
SECTIONS_DIR = ROOT / "frontend" / "src" / "content" / "technical" / "sections"


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: thiếu frontmatter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{path.name}: frontmatter không đóng")
    data: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def parse_manifest() -> list[dict[str, str]]:
    text = MANIFEST.read_text(encoding="utf-8")
    items: list[dict[str, str]] = []
    for block in text.split("{")[1:]:
        if 'id: "' not in block:
            continue
        item: dict[str, str] = {}
        for key in ("id", "title", "group", "keywords"):
            match = re.search(rf'{key}:\s*"([^"]*)"', block)
            if match:
                item[key] = match.group(1)
        order_match = re.search(r"order:\s*(\d+)", block)
        if order_match:
            item["order"] = order_match.group(1)
        if "id" in item:
            items.append(item)
    return items


def main() -> int:
    errors: list[str] = []
    manifest = parse_manifest()
    docs = []
    for path in sorted(DOCS_DIR.glob("[0-9][0-9]-*.md")):
        try:
            meta = parse_frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        meta["_file"] = path.name
        docs.append(meta)

    if len(manifest) != 20:
        errors.append(f"manifest có {len(manifest)} mục, cần 20")
    if len(docs) != 20:
        errors.append(f"docs/ky-thuat có {len(docs)} file mục, cần 20")

    manifest_by_order = {int(item["order"]): item for item in manifest if "order" in item}
    docs_by_order = {int(item["order"]): item for item in docs if "order" in item}

    for order in range(1, 21):
        m = manifest_by_order.get(order)
        d = docs_by_order.get(order)
        if not m:
            errors.append(f"manifest thiếu order {order}")
            continue
        if not d:
            errors.append(f"docs thiếu order {order}")
            continue
        for key in ("id", "title", "group"):
            if m.get(key) != d.get(key):
                errors.append(
                    f"order {order}: {key} lệch — manifest={m.get(key)!r}, docs={d.get(key)!r}"
                )
        section_files = list(SECTIONS_DIR.glob(f"{order:02d}-*.tsx"))
        if len(section_files) != 1:
            errors.append(f"order {order}: cần đúng 1 section TSX, có {len(section_files)}")

    if errors:
        print("LỖI TÀI LIỆU KỸ THUẬT:")
        for error in errors:
            print(" -", error)
        return 1

    print(f"OK: {len(docs)} mục docs khớp {len(manifest)} mục manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
