"""Kiểm tra mọi tham chiếu `§X.Y (a–b)` trong TASKS.md khớp heading của master."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs" / "kehoach" / "KE-HOACH-TONG-THE.md"
TASKS = ROOT / "docs" / "kehoach" / "TASKS.md"

REF_PATTERN = re.compile(
    r"§([0-9]+(?:\.[0-9]+)?)(?:–([0-9]+(?:\.[0-9]+)?))?[^()\n]*\(([0-9]+)–([0-9]+)\)"
)
HEADING_PATTERN = re.compile(r"^(##|###)\s+([0-9]+(?:\.[0-9]+)?)\.")


def heading_ranges(lines: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines, 1):
        match = HEADING_PATTERN.match(line)
        if match:
            headings.append((index, match.group(2), match.group(1)))

    starts = {number: line for line, number, _level in headings}
    ends: dict[str, int] = {}
    for position, (line, number, level) in enumerate(headings):
        if level == "##":
            next_top = next(
                (item[0] for item in headings[position + 1 :] if item[2] == "##"), None
            )
            ends[number] = (next_top - 1) if next_top else len(lines)
        else:
            next_any = headings[position + 1][0] if position + 1 < len(headings) else len(lines) + 1
            ends[number] = next_any - 1
    return starts, ends


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    starts, ends = heading_ranges(MASTER.read_text(encoding="utf-8").splitlines())
    text = TASKS.read_text(encoding="utf-8")

    issues: list[str] = []
    count = 0
    for match in REF_PATTERN.finditer(text):
        count += 1
        first, last = match.group(1), match.group(2)
        target = last or first
        start, end = int(match.group(3)), int(match.group(4))
        if starts.get(first) != start or ends.get(target) != end:
            issues.append(
                f"{match.group(0)} → thực tế {starts.get(first)}–{ends.get(target)}"
            )

    print(f"Đã kiểm tra {count} tham chiếu, lỗi: {len(issues)}")
    for issue in issues:
        print(" -", issue)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
