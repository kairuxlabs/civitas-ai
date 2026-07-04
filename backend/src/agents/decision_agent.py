# backend/src/agents/decision_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def decision_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    aqi_index = float(aqi.get("aqi_index") or 100)
    rain = float(weather.get("rain") or 0)
    pm25 = float(aqi.get("pm25") or 50)
    temperature = float(weather.get("temperature") or 30)

    recommendations = []
    risk_factors = 0

    # AQI thresholds (WHO guidelines)
    if aqi_index > 200:
        recommendations.append("Phát cảnh báo khẩn cấp về chất lượng không khí mức nguy hiểm")
        recommendations.append("Đóng cửa trường học và hạn chế hoạt động ngoài trời")
        recommendations.append("Triển khai trạm đo AQI di động tại các khu dân cư")
        risk_factors += 3
    elif aqi_index > 150:
        recommendations.append("Phát khuyến cáo sức khỏe về chất lượng không khí")
        recommendations.append("Hạn chế hoạt động xây dựng và phương tiện cũ")
        risk_factors += 2
    elif aqi_index > 100:
        recommendations.append("Tăng tần suất xe buýt công cộng để giảm phương tiện cá nhân")
        risk_factors += 1

    # Rain / flood thresholds
    if rain > 50:
        recommendations.append("Kích hoạt hệ thống bơm thoát nước khẩn cấp")
        recommendations.append("Phong tỏa các tuyến đường ngập — triển khai lực lượng ứng phó")
        recommendations.append("Cảnh báo sơ tán khu vực trũng thấp")
        risk_factors += 3
    elif rain > 20:
        recommendations.append("Kích hoạt hệ thống thoát nước và giám sát mực nước")
        recommendations.append("Triển khai lực lượng phân luồng giao thông tại điểm ngập")
        risk_factors += 2
    elif rain > 5:
        recommendations.append("Theo dõi công suất thoát nước, cảnh báo lái xe thận trọng")
        risk_factors += 1

    # Heat stress
    if temperature > 38:
        recommendations.append("Mở các điểm mát công cộng và tăng cường cấp nước uống miễn phí")
        recommendations.append("Cảnh báo sốc nhiệt cho người cao tuổi và lao động ngoài trời")
        risk_factors += 2
    elif temperature > 35:
        recommendations.append("Khuyến cáo hạn chế hoạt động ngoài trời từ 11h–15h")
        risk_factors += 1

    # PM2.5 specific
    if pm25 > 150:
        recommendations.append("Phân phối khẩu trang N95 tại các trung tâm y tế quận")
        risk_factors += 1

    # Citizen dissatisfaction
    citizen = state.get("citizen_analysis", "")
    if "HIGH" in citizen:
        recommendations.append("Tổ chức họp khẩn cộng đồng và mở đường dây nóng phản ánh")
        risk_factors += 1

    # Event context
    event = state.get("event_analysis", "")
    if "HIGH-impact" in event:
        recommendations.append("Tăng cường lực lượng an ninh và y tế tại điểm tổ chức sự kiện")
        risk_factors += 1

    if not recommendations:
        recommendations.append("Các chỉ số thành phố đang ổn định — duy trì giám sát thường xuyên")

    # Confidence decreases with more risk factors; penalize missing data
    has_real_data = aqi.get("aqi_index") is not None or weather.get("rain") is not None
    data_penalty = 0 if has_real_data else 10
    confidence = max(45, min(95, 92 - (risk_factors * 7) - data_penalty))

    flood_risk = "high" if rain > 20 else "moderate" if rain > 5 else "low"
    traffic_disruption = "likely" if aqi_index > 150 or rain > 10 or temperature > 38 else "unlikely"
    aqi_trend = "worsening" if aqi_index > 150 else "improving" if aqi_index < 80 else "stable"

    prediction = {
        "next_6h_aqi_trend": aqi_trend,
        "flood_risk": flood_risk,
        "traffic_disruption": traffic_disruption,
        "heat_stress": "high" if temperature > 38 else "moderate" if temperature > 35 else "low",
    }

    affected = risk_factors * 45000
    impact = {
        "population_affected": f"{affected:,} cư dân" if affected else "Không đáng kể",
        "economic_impact": "cao" if risk_factors >= 4 else "trung bình" if risk_factors >= 2 else "thấp",
        "health_risk": "cao" if aqi_index > 150 or temperature > 38 else "trung bình" if aqi_index > 100 else "thấp",
        "infrastructure_risk": "cao" if rain > 20 else "thấp",
    }

    decision = {
        "prediction": prediction,
        "impact": impact,
        "recommendations": recommendations,
        "confidence": confidence,
    }

    logger.info(f"Decision: risk_factors={risk_factors}, confidence={confidence}, flood={flood_risk}")
    return {"decision": decision, "confidence": confidence}
