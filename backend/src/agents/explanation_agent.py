# backend/src/agents/explanation_agent.py
from src.agents.base import AgentState
from src.agents.gemini_client import call_gemini
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _data_source_count(state: AgentState) -> int:
    count = 0
    if state.get("aqi_data", {}).get("aqi_index") is not None:
        count += 1
    if state.get("weather_data", {}).get("rain") is not None:
        count += 1
    if state.get("event_data"):
        count += 1
    if state.get("feedback_data"):
        count += 1
    if state.get("knowledge_summary") and "No specific SOP" not in state.get("knowledge_summary", ""):
        count += 1
    return max(count, 1)


def _rule_based_explanation(state: AgentState, confidence: float) -> list[str]:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    dec = state.get("decision", {})
    aqi_index = float(aqi.get("aqi_index") or 100)
    rain = float(weather.get("rain") or 0)
    temperature = float(weather.get("temperature") or 30)
    flood_risk = dec.get("prediction", {}).get("flood_risk", "low")
    recs = dec.get("recommendations", [])

    conditions = []
    if aqi_index > 150:
        conditions.append(f"AQI {aqi_index:.0f} mức nguy hiểm")
    elif aqi_index > 100:
        conditions.append(f"AQI {aqi_index:.0f} không tốt cho sức khỏe")
    else:
        conditions.append(f"AQI {aqi_index:.0f} chấp nhận được")

    if rain > 20:
        conditions.append(f"mưa {rain:.0f} mm/h — nguy cơ ngập cao")
    elif rain > 5:
        conditions.append(f"mưa nhẹ {rain:.0f} mm/h")

    if temperature > 38:
        conditions.append(f"nhiệt độ cực đoan {temperature:.0f}°C")
    elif temperature > 35:
        conditions.append(f"nhiệt độ cao {temperature:.0f}°C")

    sources = _data_source_count(state)
    priority = recs[0] if recs else "Duy trì giám sát thường xuyên"
    knowledge = state.get("knowledge_summary", "")

    lines = [
        f"Giao thông: {state.get('traffic_analysis', 'N/A')}",
        f"Môi trường: {state.get('environment_analysis', 'N/A')}",
        f"Sự kiện: {state.get('event_analysis', 'N/A')}",
        f"Dân cư: {state.get('citizen_analysis', 'N/A')}",
        f"Tổng quan: {'; '.join(conditions)}. Ưu tiên: {priority}.",
        f"Nguy cơ lũ: {flood_risk.upper()} | Độ tin cậy: {confidence:.0f}% ({sources} nguồn dữ liệu)",
    ]
    if knowledge and "No specific SOP" not in knowledge:
        lines.append(f"SOP tham chiếu: {knowledge[:200]}")
    return lines


def explanation_agent(state: AgentState) -> dict:
    confidence = float(state.get("confidence") or 0)
    dec = state.get("decision", {})
    recs = dec.get("recommendations", [])
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    reasoning = dec.get("reasoning", "")

    prompt = f"""Bạn là AI trợ lý đô thị Hà Nội. Hãy viết giải thích phân tích ngắn gọn, rõ ràng bằng tiếng Việt (4-5 câu) dựa trên:

DỮ LIỆU:
- AQI: {float(aqi.get('aqi_index') or 100):.0f}, PM2.5: {float(aqi.get('pm25') or 50):.1f} μg/m³
- Nhiệt độ: {float(weather.get('temperature') or 30):.1f}°C, Mưa: {float(weather.get('rain') or 0):.1f} mm/h
- Nguy cơ lũ: {dec.get('prediction', {}).get('flood_risk', 'low')}
- Tác động sức khỏe: {dec.get('impact', {}).get('health_risk', 'low')}

PHÂN TÍCH AGENT:
- Giao thông: {state.get('traffic_analysis', 'N/A')}
- Môi trường: {state.get('environment_analysis', 'N/A')}
- Sự kiện: {state.get('event_analysis', 'N/A')}
- Dân cư: {state.get('citizen_analysis', 'N/A')}

QUYẾT ĐỊNH AI: {reasoning if reasoning else 'Dựa trên phân tích đa chiều'}
ƯU TIÊN HÀNH ĐỘNG: {recs[0] if recs else 'Duy trì giám sát'}
ĐỘ TIN CẬY: {confidence:.0f}%

Yêu cầu: Đề cập số liệu cụ thể, chỉ rõ mức độ khẩn cấp, gợi ý hành động tiếp theo cho cán bộ quản lý đô thị."""

    gemini_text = call_gemini(prompt)
    sources = _data_source_count(state)

    if gemini_text:
        explanation = [
            f"Giao thông: {state.get('traffic_analysis', 'N/A')}",
            f"Môi trường: {state.get('environment_analysis', 'N/A')}",
            f"Sự kiện: {state.get('event_analysis', 'N/A')}",
            f"Dân cư: {state.get('citizen_analysis', 'N/A')}",
            f"Phân tích AI (Gemini): {gemini_text}",
            f"Độ tin cậy: {confidence:.0f}% — {sources} nguồn dữ liệu thực tế",
        ]
        knowledge = state.get("knowledge_summary", "")
        if knowledge and "No specific SOP" not in knowledge:
            explanation.append(f"SOP: {knowledge[:200]}")
    else:
        explanation = _rule_based_explanation(state, confidence)

    logger.info(f"Explanation: {len(explanation)} items, gemini={'yes' if gemini_text else 'no'}, confidence={confidence:.0f}%")
    return {"explanation": explanation}
