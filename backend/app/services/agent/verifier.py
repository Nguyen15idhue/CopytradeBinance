"""Verifier: chặn bịa số, chặn lời khuyên đầu tư, kiểm tra trader_id/đơn vị."""

import re

DISCLAIMER = "Thông tin chỉ mang tính tham khảo, không phải lời khuyên đầu tư."

ADVICE_PATTERNS = [
    r"nên (mua|bán|copy|đầu tư|tham gia|rút|nắm giữ|chốt)",
    r"khuyên (bạn|anh|chị|tôi|mình) (nên|mua|bán|copy|đầu tư)",
    r"khuyên .*?(mua|bán|copy|đầu tư)",
    r"mua ngay|bán ngay|copy ngay|đầu tư ngay",
    r"lời khuyên đầu tư",
    r"you should (buy|sell|copy|invest)",
    r"financial advice",
    r"guaranteed (profit|return)",
    r"cam kết (lợi nhuận|sinh lời)",
    r"chắc chắn (có lãi|sinh lời|lợi nhuận)",
]

INVESTMENT_ADVICE_RE = re.compile("|".join(ADVICE_PATTERNS), re.IGNORECASE)

NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?\s*(?:%|USDT|\bx\b)?", re.IGNORECASE)
TRADER_ID_RE = re.compile(r"\b\d{10,25}\b")


def contains_advice(text: str) -> bool:
    return INVESTMENT_ADVICE_RE.search(text or "") is not None


def extract_numbers(text: str) -> list[str]:
    return [m.group(0).strip() for m in NUMBER_RE.finditer(text or "")]


def _norm_number(raw: str) -> str:
    return raw.replace(",", ".").replace(" ", "").lower()


def extract_trader_ids(text: str) -> list[str]:
    return TRADER_ID_RE.findall(text or "")


DATETIME_MASK_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(:\d{2})?)?")
YEAR_RE = re.compile(r"^-?(19\d{2}|20\d{2})(%)?$")


def verify_answer(
    answer: str,
    facts: list[dict],
    row_ids: list[str] | None = None,
) -> dict:
    """Trả {answer, warnings, blocked, unverified_numbers, unknown_ids}."""
    warnings: list[str] = []
    text = answer or ""
    masked = DATETIME_MASK_RE.sub(" ", text)
    fact_values = {_norm_number(str(f.get("value", ""))) for f in facts}
    fact_blob = _norm_number(" ".join(str(f.get("value", "")) for f in facts))
    unverified: list[str] = []
    for num in extract_numbers(masked):
        norm = _norm_number(num)
        if YEAR_RE.match(norm):
            continue
        bare = re.sub(r"(%|usdt|x)$", "", norm)
        if bare == norm and re.fullmatch(r"\d{1,2}", bare):
            # Số đếm/thứ hạng không đơn vị (Top 10, 2–4 trader) — bỏ qua để đỡ nhiễu.
            continue
        if norm in fact_values or bare in fact_values or bare in fact_blob:
            continue
        unverified.append(num)
    if unverified:
        warnings.append(f"Số chưa có nguồn evidence: {', '.join(unverified[:5])}")
    unknown_ids: list[str] = []
    if row_ids is not None:
        for tid in extract_trader_ids(text):
            if tid not in set(row_ids):
                unknown_ids.append(tid)
        if unknown_ids:
            warnings.append(f"Mã trader chưa xác thực: {', '.join(unknown_ids[:5])}")
    if contains_advice(text):
        warnings.append("Phát hiện lời khuyên đầu tư — đã gắn tuyên bố miễn trừ.")
        if DISCLAIMER not in text:
            text = f"{text}\n\n_{DISCLAIMER}_".strip()
    return {
        "answer": text,
        "warnings": warnings,
        "blocked": False,
        "unverified_numbers": unverified,
        "unknown_ids": unknown_ids,
    }


def check_units(answer: str, facts: list[dict]) -> list[str]:
    """Cảnh báo khi đơn vị trong câu trả lời khác đơn vị của fact cùng giá trị."""
    warnings: list[str] = []
    unit_by_value: dict[str, str] = {}
    for fact in facts:
        unit = str(fact.get("unit") or "").strip().lower()
        if unit:
            unit_by_value[_norm_number(str(fact.get("value", "")))] = unit
    for match in NUMBER_RE.finditer(answer or ""):
        raw = match.group(0)
        lower = raw.lower()
        if "%" in lower:
            unit = "%"
        elif "usdt" in lower:
            unit = "usdt"
        elif lower.endswith("x"):
            unit = "x"
        else:
            unit = ""
        if not unit:
            continue
        bare = re.sub(r"(%|usdt|x)$", "", _norm_number(raw))
        expected = unit_by_value.get(bare)
        if expected and expected != unit:
            warnings.append(f"Đơn vị {raw} khác evidence ({expected})")
    return warnings


def build_answer_contract(
    answer: str,
    facts: list[dict],
    citations: list[dict],
    assumptions: list[str] | None = None,
    missing_data: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict:
    """Answer contract: facts/citations/assumptions/missing_data + confidence."""
    warnings = warnings or []
    if not facts:
        confidence = "low"
    elif warnings:
        confidence = "medium"
    else:
        confidence = "high"
    return {
        "answer": answer,
        "facts": facts,
        "citations": citations,
        "assumptions": assumptions or [],
        "missing_data": missing_data or [],
        "confidence": confidence,
        "warnings": warnings,
    }
