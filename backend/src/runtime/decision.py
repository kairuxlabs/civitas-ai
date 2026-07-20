# backend/src/runtime/decision.py
"""Decision runtime: aggregates worker outputs into the spec_v2 §9 shape:
{summary, prediction, risk, recommendation, confidence, evidence}.
"""
import asyncio

from src.agents.gemini_client import call_gemini, parse_json_safe
from src.reasoning import critic
from src.runtime.event_bus import Event, EventBus, EventTypes
from src.runtime.state import RunState, TaskStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)

_REQUIRED_KEYS = {"summary", "prediction", "risk", "recommendation", "confidence"}

_DECISION_PROMPT = """You are the Decision runtime of CityOS, managing Hanoi.
Goal: {goal}

Agent findings:
{findings}

Reflection: {reflection}

Respond in Vietnamese. Output ONLY JSON:
{{"summary": str, "prediction": str, "risk": "low"|"medium"|"high",
"recommendation": [str], "confidence": number 0-100, "evidence": []}}
"""


def _evidence(run: RunState) -> list[dict]:
    items: list[dict] = []
    for t in run.tasks.values():
        if t.status != TaskStatus.DONE or not t.result:
            continue
        items.append({
            "task": t.spec.id,
            "agent": t.spec.agent,
            "summary": t.result.get("summary", ""),
            "confidence": t.result.get("confidence"),
        })
        items.extend(t.result.get("evidence", []))
    return items


def _fallback_decision(run: RunState) -> dict:
    flood_risk = run.context.get("flood_risk", "low")
    aqi = float((run.context.get("aqi_data") or {}).get("aqi_index") or 0)
    rain = float((run.context.get("weather_data") or {}).get("rain") or 0)
    emergency = run.context.get("emergency") or {}
    knowledge = (run.context.get("knowledge_summary") or "").strip()

    risk = "high" if flood_risk == "high" or aqi > 200 else \
        "medium" if flood_risk == "medium" or aqi > 150 else "low"

    recommendation: list[str] = []
    if flood_risk == "high":
        recommendation += [
            "Kích hoạt toàn bộ trạm bơm thoát nước tại các quận trũng",
            "Phong tỏa và phân luồng các tuyến đường có nguy cơ ngập sâu",
        ]
    elif flood_risk == "medium":
        recommendation.append("Kích hoạt hệ thống thoát nước và giám sát mực nước")
    if aqi > 150:
        recommendation.append("Phát khuyến cáo sức khỏe về chất lượng không khí")
    recommendation += [f"Triển khai: {u}" for u in emergency.get("units", [])[:3]]
    if knowledge:
        recommendation.append(f"Áp dụng SOP: {knowledge[:120]}")
    if not recommendation:
        recommendation.append("Các chỉ số ổn định — duy trì giám sát thường xuyên")

    reflection = run.context.get("reflection") or {}
    avg_conf = float(reflection.get("avg_confidence", 0.6))
    confidence = max(40.0, min(95.0, avg_conf * 100 - len(reflection.get("missing", [])) * 10))

    forecast = run.context.get("forecast") or {}
    prediction = (
        f"Mưa 6h tới ~{forecast.get('rain_6h', rain)}mm/h, AQI ~{forecast.get('aqi_6h', aqi)}"
        if forecast else
        f"Rủi ro ngập {flood_risk}, AQI hiện tại {aqi:.0f}"
    )

    return {
        "summary": f"Mục tiêu: {run.goal}. Rủi ro tổng hợp: {risk}.",
        "prediction": prediction,
        "risk": risk,
        "recommendation": recommendation,
        "confidence": round(confidence, 1),
    }


async def make_decision(run: RunState, bus: EventBus) -> dict:
    findings = "\n".join(
        f"- {t.spec.agent}: {(t.result or {}).get('summary', '')}"
        for t in run.tasks.values() if t.status == TaskStatus.DONE
    )
    prompt = _DECISION_PROMPT.format(
        goal=run.goal, findings=findings or "(none)",
        reflection=run.context.get("reflection", {}),
    )

    decision: dict | None = None
    text = await asyncio.to_thread(call_gemini, prompt, True)
    if text:
        parsed = parse_json_safe(text)
        if parsed and _REQUIRED_KEYS <= set(parsed):
            try:
                parsed["confidence"] = max(0.0, min(100.0, float(parsed["confidence"])))
                if not isinstance(parsed["recommendation"], list):
                    parsed["recommendation"] = [str(parsed["recommendation"])]
                decision = parsed
            except (TypeError, ValueError):
                decision = None
        if decision is None:
            logger.warning("Decision: Gemini output invalid, falling back to rules")

    if decision is None:
        decision = _fallback_decision(run)

    decision["evidence"] = _evidence(run)
    critic_result = critic.review(decision, decision["evidence"])
    decision["confidence"] = critic_result["confidence"]
    decision["critic_notes"] = critic_result["critic_notes"]
    run.log(f"Decision ready (confidence {decision['confidence']:.0f}%)", actor="decision")
    await bus.publish(Event(
        type=EventTypes.DECISION_READY,
        payload={"risk": decision["risk"], "confidence": decision["confidence"], "summary": decision["summary"]},
        run_id=run.run_id,
        source="decision",
    ))
    return decision
