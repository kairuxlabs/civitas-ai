# backend/src/agents/explanation_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _gemini_explanation(state: AgentState, confidence: float) -> list[str] | None:
    """Try to generate explanation via Gemini. Returns None if unavailable."""
    try:
        from src.utils.config import settings
        if not settings.gemini_api_key:
            return None

        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        aqi = state.get("aqi_data", {})
        weather = state.get("weather_data", {})
        dec = state.get("decision", {})
        recs = dec.get("recommendations", [])

        prompt = f"""Bạn là AI phân tích đô thị cho thành phố Hà Nội. Hãy viết giải thích ngắn gọn (3–4 câu, bằng tiếng Việt) về tình huống hiện tại dựa trên dữ liệu sau:

- AQI: {aqi.get('aqi_index', 'N/A')} | PM2.5: {aqi.get('pm25', 'N/A')} μg/m³
- Nhiệt độ: {weather.get('temperature', 'N/A')}°C | Lượng mưa: {weather.get('rain', 'N/A')} mm/h
- Phân tích giao thông: {state.get('traffic_analysis', 'N/A')}
- Phân tích môi trường: {state.get('environment_analysis', 'N/A')}
- Sự kiện: {state.get('event_analysis', 'N/A')}
- Dân cư: {state.get('citizen_analysis', 'N/A')}
- Khuyến nghị hàng đầu: {recs[0] if recs else 'N/A'}
- Độ tin cậy phân tích: {confidence:.0f}%

Yêu cầu: Súc tích, có số liệu cụ thể, chỉ rõ mức độ ưu tiên hành động."""

        response = model.generate_content(prompt, generation_config={"max_output_tokens": 300})
        gemini_text = response.text.strip()

        return [
            f"Giao thông: {state.get('traffic_analysis', 'N/A')}",
            f"Môi trường: {state.get('environment_analysis', 'N/A')}",
            f"Sự kiện: {state.get('event_analysis', 'N/A')}",
            f"Dân cư: {state.get('citizen_analysis', 'N/A')}",
            f"Phân tích AI: {gemini_text}",
            f"Độ tin cậy: {confidence:.0f}% — dựa trên {_data_source_count(state)} nguồn dữ liệu thực",
        ]
    except Exception as e:
        logger.warning(f"Gemini explanation failed: {e}")
        return None


def _data_source_count(state: AgentState) -> int:
    """Count how many data sources actually have non-default data."""
    count = 0
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    if aqi.get("aqi_index") is not None:
        count += 1
    if weather.get("rain") is not None:
        count += 1
    if state.get("event_data"):
        count += 1
    if state.get("feedback_data"):
        count += 1
    if state.get("knowledge_summary") and "No specific SOP" not in state.get("knowledge_summary", ""):
        count += 1
    return max(count, 1)


def _rule_based_explanation(state: AgentState, confidence: float) -> list[str]:
    """Fallback explanation without Gemini."""
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    dec = state.get("decision", {})

    aqi_index = float(aqi.get("aqi_index") or 100)
    rain = float(weather.get("rain") or 0)
    temperature = float(weather.get("temperature") or 30)
    flood_risk = dec.get("prediction", {}).get("flood_risk", "low")
    recs = dec.get("recommendations", [])

    # Build context-sensitive summary
    conditions = []
    if aqi_index > 150:
        conditions.append(f"AQI {aqi_index:.0f} ở mức nguy hiểm")
    elif aqi_index > 100:
        conditions.append(f"AQI {aqi_index:.0f} ở mức không tốt cho sức khoẻ")
    else:
        conditions.append(f"AQI {aqi_index:.0f} ở mức chấp nhận được")

    if rain > 20:
        conditions.append(f"mưa lớn {rain:.0f} mm/h — nguy cơ ngập cao")
    elif rain > 5:
        conditions.append(f"mưa vừa {rain:.0f} mm/h")

    if temperature > 38:
        conditions.append(f"nhiệt độ cực đoan {temperature:.0f}°C")
    elif temperature > 35:
        conditions.append(f"nhiệt độ cao {temperature:.0f}°C")

    condition_str = "; ".join(conditions) if conditions else "điều kiện thời tiết bình thường"

    priority_action = recs[0] if recs else "Duy trì giám sát thường xuyên"
    sources = _data_source_count(state)

    knowledge = state.get("knowledge_summary", "")

    lines = [
        f"Giao thông: {state.get('traffic_analysis', 'N/A')}",
        f"Môi trường: {state.get('environment_analysis', 'N/A')}",
        f"Sự kiện: {state.get('event_analysis', 'N/A')}",
        f"Dân cư: {state.get('citizen_analysis', 'N/A')}",
        f"Tổng quan: Quận đang ghi nhận {condition_str}. Ưu tiên hành động: {priority_action}.",
        f"Nguy cơ lũ lụt: {flood_risk.upper()} | Độ tin cậy phân tích: {confidence:.0f}% ({sources} nguồn dữ liệu)",
    ]
    if knowledge and "No specific SOP" not in knowledge:
        lines.append(f"Quy trình tham chiếu: {knowledge[:200]}")
    return lines


def explanation_agent(state: AgentState) -> dict:
    confidence = float(state.get("confidence") or 0)

    explanation = _gemini_explanation(state, confidence)
    if explanation is None:
        explanation = _rule_based_explanation(state, confidence)

    logger.info(f"Explanation: {len(explanation)} items, confidence={confidence:.0f}%")
    return {"explanation": explanation}
