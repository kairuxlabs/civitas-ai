# backend/src/simulation/profiles.py
"""Scenario profiles for the Digital Twin simulation engine (spec_v2 §12)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioProfile:
    name: str
    label: str
    rain_range: tuple[float, float]
    aqi_range: tuple[float, float]
    temp_range: tuple[float, float]
    negative_feedback_ratio: float
    feedback_pool: list[tuple[str, str, str]] = field(default_factory=list)  # (category, sentiment, content)
    event_templates: list[tuple[str, str, str]] = field(default_factory=list)  # (title, category, impact_level)
    event_chance: float = 0.05


PROFILES: dict[str, ScenarioProfile] = {
    "normal": ScenarioProfile(
        name="normal",
        label="Bình thường",
        rain_range=(0, 2),
        aqi_range=(60, 110),
        temp_range=(28, 34),
        negative_feedback_ratio=0.3,
        feedback_pool=[
            ("traffic", "negative", "Tắc nhẹ giờ cao điểm tại nút giao lớn"),
            ("environment", "positive", "Không khí dễ chịu, phù hợp hoạt động ngoài trời"),
            ("infrastructure", "positive", "Đèn đường hoạt động ổn định"),
            ("safety", "positive", "Khu vực an ninh tốt"),
        ],
        event_templates=[("Hoạt động cộng đồng cuối tuần", "community", "low")],
        event_chance=0.05,
    ),
    "heavy_rain": ScenarioProfile(
        name="heavy_rain",
        label="Mưa lớn",
        rain_range=(25, 70),
        aqi_range=(50, 95),
        temp_range=(24, 29),
        negative_feedback_ratio=0.75,
        feedback_pool=[
            ("flood", "negative", "Ngập úng sâu tại nhiều tuyến phố sau mưa lớn"),
            ("flood", "negative", "Nước tràn vào nhà dân khu vực trũng"),
            ("traffic", "negative", "Ùn tắc nghiêm trọng do mưa ngập"),
            ("infrastructure", "negative", "Cống thoát nước quá tải"),
        ],
        event_templates=[
            ("Cảnh báo ngập úng diện rộng", "flood", "high"),
            ("Cây đổ chắn ngang đường do mưa dông", "incident", "medium"),
        ],
        event_chance=0.3,
    ),
    "air_pollution": ScenarioProfile(
        name="air_pollution",
        label="Ô nhiễm không khí",
        rain_range=(0, 1),
        aqi_range=(160, 260),
        temp_range=(30, 36),
        negative_feedback_ratio=0.7,
        feedback_pool=[
            ("environment", "negative", "Không khí ngột ngạt, khói bụi dày đặc"),
            ("environment", "negative", "Trẻ nhỏ ho nhiều do ô nhiễm"),
            ("environment", "negative", "Tầm nhìn giảm vì sương bụi mịn"),
        ],
        event_templates=[("Chỉ số AQI vượt ngưỡng nguy hại", "environment", "high")],
        event_chance=0.2,
    ),
    "heatwave": ScenarioProfile(
        name="heatwave",
        label="Nắng nóng gay gắt",
        rain_range=(0, 0.5),
        aqi_range=(110, 170),
        temp_range=(37, 42),
        negative_feedback_ratio=0.6,
        feedback_pool=[
            ("environment", "negative", "Nắng nóng gay gắt, nguy cơ sốc nhiệt"),
            ("infrastructure", "negative", "Nhu cầu điện tăng vọt, lo ngại quá tải"),
        ],
        event_templates=[("Cảnh báo nắng nóng đặc biệt gay gắt", "weather", "medium")],
        event_chance=0.15,
    ),
    "major_event": ScenarioProfile(
        name="major_event",
        label="Sự kiện đông người",
        rain_range=(0, 5),
        aqi_range=(100, 150),
        temp_range=(28, 34),
        negative_feedback_ratio=0.5,
        feedback_pool=[
            ("traffic", "negative", "Đông nghẹt người đổ về khu vực lễ hội"),
            ("safety", "negative", "Lo ngại chen lấn tại điểm tổ chức sự kiện"),
            ("traffic", "negative", "Bãi gửi xe quá tải quanh khu sự kiện"),
        ],
        event_templates=[
            ("Lễ hội lớn tại trung tâm thành phố", "festival", "high"),
            ("Sự kiện thể thao đông khán giả", "event", "medium"),
        ],
        event_chance=0.5,
    ),
}
