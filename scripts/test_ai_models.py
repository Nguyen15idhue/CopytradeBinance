"""Kiểm tra kết nối + chất lượng 2 model OpenRouter trong .env.

Chạy: python scripts/test_ai_models.py
Không in API key. Ghi báo cáo docs/kehoach/AI-MODEL-TEST.md.
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
REPORT_PATH = ROOT / "docs" / "kehoach" / "AI-MODEL-TEST.md"

REQUIRED_KEYS = {"summary", "strengths", "weaknesses", "risk_flags", "missing_data", "evidence_ids"}
ADVICE_PATTERNS = [
    r"nên (mua|bán|đầu tư|copy)",
    r"khuyến nghị (mua|bán|đầu tư|copy)",
    r"chắc chắn (thắng|lãi|sinh lời)",
    r"cam kết lợi nhuận",
]

TRADER_A = {
    "id": "5143921081414022657",
    "tier": "qualified_upper",
    "roi_90d": 30.3,
    "mdd_90d": 6.52,
    "sharpe": 3.83,
    "win_rate_order": 99.64,
    "total_orders": 1234,
    "max_leverage": 10.0,
    "worst_position_roi": -88.5,
    "profit_factor": None,
    "runtime_days": 691.0,
    "confidence": 0.89,
    "risk_level": "high",
    "benchmark_return": None,
}

TRADER_B = {
    "id": "5296057151807357697",
    "tier": "excluded",
    "roi_90d": 61.75,
    "mdd_90d": 31.34,
    "sharpe": None,
    "win_rate_order": 50.0,
    "total_orders": 10,
    "max_leverage": 15.0,
    "worst_position_roi": -97.8,
    "profit_factor": 1.64,
    "runtime_days": 4.11,
    "confidence": 0.31,
    "risk_level": "critical",
    "benchmark_return": None,
}

PROMPT = """Bạn là trợ lý phân tích dữ liệu copy-trading. Chỉ trả về JSON hợp lệ, không markdown.
Dữ liệu trader (đã chuẩn hóa):
{trader}

Hãy trả JSON đúng schema:
{{
  "summary": "3 câu, chỉ dựa trên dữ liệu trên",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "risk_flags": ["..."],
  "missing_data": ["..."],
  "evidence_ids": ["<id field hoặc tên chỉ số đã dùng>"]
}}
Quy tắc bắt buộc:
- Không đưa lời khuyên đầu tư, không hứa hẹn lợi nhuận.
- Nêu rõ chỉ số bị null trong missing_data.
- Mọi nhận định phải tham chiếu chỉ số trong evidence_ids.
"""


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def parse_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def evaluate(payload: dict[str, Any] | None, trader: dict[str, Any], invoked: str) -> dict[str, Any]:
    scores: dict[str, int] = {}
    notes: list[str] = []
    if payload is None:
        return {
            "scores": {key: 0 for key in ("json", "schema", "evidence", "risk", "uncertainty", "no_advice")},
            "total": 0,
            "notes": ["Không parse được JSON"],
        }

    scores["json"] = 5
    missing_keys = REQUIRED_KEYS - set(payload)
    scores["schema"] = 5 if not missing_keys else max(0, 5 - 2 * len(missing_keys))
    if missing_keys:
        notes.append(f"thiếu key: {sorted(missing_keys)}")

    evidence = payload.get("evidence_ids") or []
    evidence_ok = any(str(trader["id"]) in str(item) for item in evidence) or any(
        token in str(evidence).lower()
        for token in ("roi", "mdd", "leverage", "runtime", "sharpe", "confidence")
    )
    scores["evidence"] = 5 if evidence_ok and evidence else 2 if evidence else 0

    risk_text = " ".join(str(item) for item in payload.get("risk_flags") or []).lower()
    risk_hits = sum(
        1
        for token in ("mdd", "leverage", "drawdown", "rủi ro", "risk")
        if token in risk_text
    )
    scores["risk"] = min(5, risk_hits * 2)

    missing_text = " ".join(str(item) for item in payload.get("missing_data") or []).lower()
    expected_missing = []
    if trader.get("sharpe") is None:
        expected_missing.append("sharpe")
    if trader.get("benchmark_return") is None:
        expected_missing.append("benchmark")
    if trader.get("profit_factor") is None:
        expected_missing.append("profit")
    found = sum(1 for token in expected_missing if token in missing_text)
    scores["uncertainty"] = 5 if expected_missing and found == len(expected_missing) else (
        3 if found else 0
    )

    whole = json.dumps(payload, ensure_ascii=False).lower()
    advices = [pattern for pattern in ADVICE_PATTERNS if re.search(pattern, whole)]
    scores["no_advice"] = 0 if advices else 5
    if advices:
        notes.append(f"có lời khuyên đầu tư: {advices}")

    total = sum(scores.values())
    return {"scores": scores, "total": total, "notes": notes, "payload": payload}


def call_model(client: httpx.Client, env: dict[str, str], model: str, trader: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 2500,
        "reasoning": {"effort": "low"},
        "messages": [
            {"role": "system", "content": "Chỉ trả JSON hợp lệ, không giải thích ngoài JSON."},
            {"role": "user", "content": PROMPT.format(trader=json.dumps(trader, ensure_ascii=False))},
        ],
    }
    headers = {
        "Authorization": f"Bearer {env['OPENROUTER_API_KEY']}",
        "HTTP-Referer": "http://localhost:8090",
        "X-Title": "CopytradeBinance AI test",
    }

    started = time.perf_counter()
    last: dict[str, Any] = {}
    for attempt in range(2):
        try:
            response = client.post(
                f"{env.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')}/chat/completions",
                headers=headers,
                json=payload,
            )
        except httpx.HTTPError as exc:
            last = {"ok": False, "error": f"network: {exc}", "latency_ms": round((time.perf_counter() - started) * 1000)}
            time.sleep(3)
            continue

        latency = round((time.perf_counter() - started) * 1000)
        if response.status_code == 200:
            body = response.json()
            choice = (body.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content") or ""
            return {
                "ok": True,
                "status": 200,
                "latency_ms": latency,
                "usage": body.get("usage") or {},
                "content": content,
                "model_returned": body.get("model"),
                "attempts": attempt + 1,
            }
        last = {
            "ok": False,
            "status": response.status_code,
            "error": response.text[:400],
            "latency_ms": latency,
            "attempts": attempt + 1,
        }
        if response.status_code not in (429, 500, 502, 503):
            break
        time.sleep(6)
    return last


def main() -> int:
    env = load_env()
    if not env.get("OPENROUTER_API_KEY"):
        print("THIẾU OPENROUTER_API_KEY trong .env")
        return 1
    models = {
        "primary": env.get("AI_MODEL_PRIMARY", ""),
        "fallback": env.get("AI_MODEL_FALLBACK", ""),
    }
    timeout = float(env.get("AI_TIMEOUT_SECONDS", "60"))

    results: dict[str, Any] = {"models": models, "cases": {}}
    with httpx.Client(timeout=timeout) as client:
        try:
            key_info = client.get(
                f"{env.get('OPENROUTER_BASE_URL')}/key",
                headers={"Authorization": f"Bearer {env['OPENROUTER_API_KEY']}"},
            )
            results["key"] = {"status": key_info.status_code, "body": key_info.json() if key_info.status_code == 200 else key_info.text[:200]}
        except httpx.HTTPError as exc:
            results["key"] = {"status": None, "error": str(exc)}

        for label, model in models.items():
            if not model:
                results["cases"][label] = {"error": "model id trống"}
                continue
            case_results = {}
            for case_name, trader in (("rich_data", TRADER_A), ("young_portfolio", TRADER_B)):
                call = call_model(client, env, model, trader)
                if not call.get("ok"):
                    case_results[case_name] = call
                    continue
                parsed = parse_json(call["content"])
                evaluation = evaluate(parsed, trader, model)
                evaluation.update(
                    {
                        "latency_ms": call["latency_ms"],
                        "usage": call.get("usage"),
                        "model_returned": call.get("model_returned"),
                        "raw": call["content"][:1500],
                    }
                )
                case_results[case_name] = evaluation
            results["cases"][label] = case_results

    print(json.dumps({k: v for k, v in results.items() if k != "key"}, ensure_ascii=False, indent=2)[:4000])
    write_report(results)
    return 0


def write_report(results: dict[str, Any]) -> None:
    lines = [
        "# AI MODEL TEST — OpenRouter",
        "",
        "> Sinh tự động bởi `scripts/test_ai_models.py`.",
        "",
        "## Cấu hình",
        "",
        f"- Primary: `{results['models'].get('primary') or '(trống)'}`",
        f"- Fallback: `{results['models'].get('fallback') or '(trống)'}`",
        f"- Key check: HTTP `{(results.get('key') or {}).get('status')}`",
        "",
    ]
    for label, cases in results["cases"].items():
        lines += [f"## Model {label}", ""]
        if isinstance(cases, dict) and cases.get("error"):
            lines += [f"Lỗi: {cases['error']}", ""]
            continue
        for case_name, data in cases.items():
            lines.append(f"### Case `{case_name}`")
            if not data.get("ok", True):
                lines += [
                    f"- Kết quả: **FAIL**",
                    f"- HTTP: `{data.get('status')}`",
                    f"- Lỗi: `{str(data.get('error'))[:300]}`",
                    f"- Latency: {data.get('latency_ms')} ms",
                    "",
                ]
                continue
            scores = data["scores"]
            lines += [
                f"- Kết quả: **PASS**",
                f"- Latency: {data['latency_ms']} ms",
                f"- Tokens: prompt `{(data.get('usage') or {}).get('prompt_tokens')}`, "
                f"completion `{(data.get('usage') or {}).get('completion_tokens')}`",
                f"- Điểm chất lượng: **{data['total']}/30**",
                f"- Chi tiết: {scores}",
            ]
            if data.get("notes"):
                lines.append(f"- Ghi chú: {'; '.join(data['notes'])}")
            lines += ["", "```json", json.dumps(data.get("payload"), ensure_ascii=False, indent=2)[:1500], "```", ""]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Đã ghi {REPORT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
