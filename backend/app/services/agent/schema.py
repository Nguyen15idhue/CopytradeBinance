"""Contract dùng chung cho agent: tool result, answer, SSE event."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EvidenceItem:
    id: str
    label: str
    value: Any
    unit: str | None = None
    source: str = "database"
    as_of: str | None = None
    row_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "as_of": self.as_of,
            "row_id": self.row_id,
        }


@dataclass
class ToolResult:
    data: Any = None
    meta: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceItem] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "meta": self.meta,
            "evidence": [item.to_dict() for item in self.evidence],
            "error": self.error,
        }

    @classmethod
    def fail(cls, message: str) -> "ToolResult":
        return cls(data=None, error=message)


@dataclass
class AgentAnswer:
    answer: str
    facts: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    confidence: str = "medium"
    next_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "facts": self.facts,
            "citations": self.citations,
            "assumptions": self.assumptions,
            "missing_data": self.missing_data,
            "confidence": self.confidence,
            "next_actions": self.next_actions,
        }


@dataclass
class SseEvent:
    event: str
    data: dict[str, Any]

    def encode(self) -> str:
        import json

        return f"event: {self.event}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


SSE_EVENTS = (
    "token",
    "tool_call",
    "tool_result",
    "citation",
    "warning",
    "done",
    "error",
)


def utcnow_iso() -> str:
    return datetime.now().astimezone().isoformat()
