"""Schema JSON cho AI report + kiểm tra an toàn."""

import re

from pydantic import BaseModel, Field, field_validator

ADVICE_PATTERNS = [
    r"nên (mua|bán|đầu tư|copy)",
    r"khuyến nghị (mua|bán|đầu tư|copy)",
    r"chắc chắn (thắng|lãi|sinh lời)",
    r"cam kết lợi nhuận",
    r"all[- ]in",
]


class AIReportPayload(BaseModel):
    summary: str = Field(min_length=20, max_length=2000)
    strengths: list[str] = Field(min_length=1, max_length=8)
    weaknesses: list[str] = Field(min_length=1, max_length=8)
    risk_flags: list[str] = Field(default_factory=list, max_length=10)
    missing_data: list[str] = Field(default_factory=list, max_length=10)
    evidence_ids: list[str] = Field(min_length=1, max_length=30)

    @field_validator("summary", "strengths", "weaknesses", "risk_flags")
    @classmethod
    def no_investment_advice(cls, value):
        text = " ".join(value) if isinstance(value, list) else value
        for pattern in ADVICE_PATTERNS:
            if re.search(pattern, text.lower()):
                raise ValueError("report chứa lời khuyên đầu tư")
        return value
