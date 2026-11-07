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

NUMBER_PATTERN = re.compile(r"\d")


class AIReportPayload(BaseModel):
    summary: str = Field(min_length=20, max_length=2000)
    strengths: list[str] = Field(min_length=1, max_length=8)
    weaknesses: list[str] = Field(min_length=1, max_length=8)
    risk_flags: list[str] = Field(default_factory=list, max_length=10)
    missing_data: list[str] = Field(default_factory=list, max_length=10)
    evidence_ids: list[str] = Field(min_length=1, max_length=30)

    @field_validator("summary")
    @classmethod
    def summary_has_numbers(cls, value: str) -> str:
        if len(NUMBER_PATTERN.findall(value)) < 2:
            raise ValueError("summary phải có ít nhất 2 số liệu")
        return value

    @field_validator("strengths", "weaknesses")
    @classmethod
    def lists_have_numbers(cls, value: list[str]) -> list[str]:
        if not any(NUMBER_PATTERN.search(item) for item in value):
            raise ValueError("mỗi danh sách điểm mạnh/điểm cần lưu ý phải có ít nhất 1 số liệu")
        return value

    @field_validator("summary", "strengths", "weaknesses", "risk_flags")
    @classmethod
    def no_investment_advice(cls, value):
        text = " ".join(value) if isinstance(value, list) else value
        for pattern in ADVICE_PATTERNS:
            if re.search(pattern, text.lower()):
                raise ValueError("report chứa lời khuyên đầu tư")
        return value
