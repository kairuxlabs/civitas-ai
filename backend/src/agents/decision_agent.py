# backend/src/agents/decision_agent.py
from src.agents.base import AgentState
from src.agents.gemini_client import call_gemini, parse_json_safe
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _rule_based_decision(state: AgentState) -> dict:
    """Fallback rule-based decision when Gemini is unavailable."""
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    aqi_index = float(aqi.get("aqi_index") or 100)
    rain = float(weather.get("rain") or 0)
    pm25 = float(aqi.get("pm25") or 50)
    temperature = float(weather.get("temperature") or 30)

    recommendations = []
    risk_factors = 0

    if aqi_index > 200:
        recommendations += [
            "Phát cảnh báo khẩn cấp về chất lượng không khí mức nguy hiểm",
            "Đóng cửa trường học và hạn chế hoạt động ngoài trời",
        ]
        risk_factors += 3
    elif aqi_index > 150:
        recommendations += [
            "Phát khuyến cáo sức khỏe về chất lượng không khí",
            "Hạn chế hoạt động xây dựng và phương tiện cũ",
        ]
        risk_factors += 2
    elif aqi_index > 100:
        recommendations.append("Tăng tần suất xe buýt để giảm phương tiện cá nhân")
        risk_factors += 1

    if rain > 50:
        recommendations += [
            "Kích hoạt hệ thống bơm thoát nước khẩn cấp",
            "Phong tỏa các tuyến đường ngập — triển khai lực lượng ứng phó",
        ]
        risk_factors += 3
    elif rain > 20:
        recommendations += [
            "Kích hoạt hệ thống thoát nước và giám sát mực nước",
            "Triển khai lực lượng phân luồng tại điểm ngập",
        ]
        risk_factors += 2
    elif rain > 5:
        recommendations.append("Theo dõi công suất thoát nước, cảnh báo lái xe thận trọng")
        risk_factors += 1

    if temperature > 38:
        recommendations += [
            "Mở điểm mát công cộng và tăng cường cấp nước uống",
            "Cảnh báo sốc nhiệt cho người cao tuổi và lao động ngoài trời",
        ]
        risk_factors += 2
    elif temperature > 35:
        recommendations.append("Khuyến cáo hạn chế hoạt động ngoài trời từ 11h–15h")
        risk_factors += 1

    if pm25 > 150:
        recommendations.append("Phân phối khẩu trang N95 tại các trung tâm y tế quận")
        risk_factors += 1

    if "HIGH" in state.get("citizen_analysis", ""):
        recommendations.append("Tổ chức họp khẩn cộng đồng và mở đường dây nóng")
        risk_factors += 1
    if "HIGH-impact" in state.get("event_analysis", ""):
        recommendations.append("Tăng cường lực lượng an ninh và y tế tại sự kiện")
        risk_factors += 1

    if not recommendations:
        recommendations.append("Các chỉ số thành phố ổn định — duy trì giám sát thường xuyên")

    has_real_data = aqi.get("aqi_index") is not None or weather.get("rain") is not None
    data_penalty = 0 if has_real_data else 10
    confidence = max(45, min(92, 92 - (risk_factors * 7) - data_penalty))

    return {
        "prediction": {
            "next_6h_aqi_trend": "worsening" if aqi_index > 150 else "improving" if aqi_index < 80 else "stable",
            "flood_risk": "high" if rain > 20 else "moderate" if rain > 5 else "low",
            "traffic_disruption": "likely" if aqi_index > 150 or rain > 10 else "unlikely",
            "heat_stress": "high" if temperature > 38 else "moderate" if temperature > 35 else "low",
        },
        "impact": {
            "population_affected": f"{risk_factors * 45000:,} cư dân" if risk_factors else "Không đáng kể",
            "economic_impact": "cao" if risk_factors >= 4 else "trung bình" if risk_factors >= 2 else "thấp",
            "health_risk": "cao" if aqi_index > 150 or temperature > 38 else "trung bình" if aqi_index > 100 else "thấp",
            "infrastructure_risk": "cao" if rain > 20 else "thấp",
        },
        "recommendations": recommendations,
        "confidence": confidence,
    }


def _collect_evidence(state: AgentState) -> list[dict]:
    fields = ("traffic_evidence", "environment_evidence", "event_evidence",
              "citizen_evidence", "knowledge_evidence")
    items = [item for field in fields for item in state.get(field, [])]
    for i, item in enumerate(items):
        item["id"] = f"ev-{i + 1}"
    return items


def decision_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})

    prompt = f"""Bạn là AI phân tích đô thị cho Hà Nội. Dựa trên dữ liệu cảm biến và phân tích từ các agent chuyên biệt, hãy đưa ra quyết định quản lý đô thị.

DỮ LIỆU CẢM BIẾN:
- AQI: {float(aqi.get('aqi_index') or 100):.0f} | PM2.5: {float(aqi.get('pm25') or 50):.1f} μg/m³ | PM10: {float(aqi.get('pm10') or 80):.1f} μg/m³
- Nhiệt độ: {float(weather.get('temperature') or 30):.1f}°C | Độ ẩm: {float(weather.get('humidity') or 70):.0f}% | Mưa: {float(weather.get('rain') or 0):.1f} mm/h

PHÂN TÍCH TỪNG AGENT:
- Giao thông: {state.get('traffic_analysis', 'N/A')}
- Môi trường: {state.get('environment_analysis', 'N/A')}
- Sự kiện: {state.get('event_analysis', 'N/A')}
- Dân cư: {state.get('citizen_analysis', 'N/A')}
- Kiến thức SOP: {state.get('knowledge_summary', 'N/A')}

CÂU HỎI: {state.get('query', '')}

Trả về JSON theo đúng định dạng sau (không thêm text ngoài JSON):
{{
  "prediction": {{
    "next_6h_aqi_trend": "worsening|stable|improving",
    "flood_risk": "high|moderate|low",
    "traffic_disruption": "likely|unlikely",
    "heat_stress": "high|moderate|low",
    "summary": "1 câu tóm tắt dự báo bằng tiếng Việt"
  }},
  "impact": {{
    "population_affected": "số lượng và mô tả ngắn",
    "economic_impact": "cao|trung bình|thấp",
    "health_risk": "cao|trung bình|thấp",
    "infrastructure_risk": "cao|thấp",
    "detail": "1 câu mô tả tác động cụ thể"
  }},
  "recommendations": [
    "khuyến nghị cụ thể 1 (ưu tiên cao nhất)",
    "khuyến nghị cụ thể 2",
    "khuyến nghị cụ thể 3"
  ],
  "confidence": 75,
  "reasoning": "1-2 câu giải thích lý do độ tin cậy này"
}}

Lưu ý: confidence từ 45-95 dựa trên mức độ rủi ro và chất lượng dữ liệu."""

    evidence = _collect_evidence(state)

    raw = call_gemini(prompt, expect_json=True)
    if raw:
        parsed = parse_json_safe(raw)
        if parsed and "recommendations" in parsed and "confidence" in parsed:
            confidence = float(parsed.get("confidence", 70))
            logger.info(f"Gemini decision: confidence={confidence:.0f}%, recommendations={len(parsed['recommendations'])}")
            return {"decision": parsed, "confidence": confidence, "evidence": evidence}
        logger.warning(f"Gemini returned invalid JSON, falling back. Raw: {raw[:200]}")

    # Fallback to rule-based
    decision = _rule_based_decision(state)
    logger.info(f"Rule-based decision: confidence={decision['confidence']:.0f}%")
    return {"decision": decision, "confidence": decision["confidence"], "evidence": evidence}
