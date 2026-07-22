# backend/src/simulation/profiles.py
"""Scenario profiles for the Digital Twin simulation engine (spec_v2 §12).

Each non-"normal" profile owns its own auto-goal trigger condition and goal
text via `goal_trigger`/`goal_text`, instead of the engine applying one
rain/AQI threshold pair to every scenario. That used to mean "heatwave"
never auto-triggered (nothing checked temperature) and "major_event" never
did either (nothing checked crowd risk) — both scenarios' actual danger
signal was silently ignored.
"""
import random
from dataclasses import dataclass, field
from typing import Callable

from src.reasoning.thresholds import FLOOD_RISK_HIGH_RAIN_MM

# AQI (US EPA index) above which air quality is "unhealthy" — the trigger
# point for the air_pollution scenario's auto-goal.
AQI_POLLUTION_THRESHOLD = 150.0

# Temperature (°C) above which conditions are "extreme heat" — the trigger
# point for the heatwave scenario's auto-goal.
HEATWAVE_TEMP_THRESHOLD_C = 38.0


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
    # Reads current simulated values (+ this profile, for event_chance-style
    # trigers) and decides whether this tick should auto-submit a goal. None
    # means the scenario never auto-triggers (e.g. "normal").
    goal_trigger: Callable[[dict, "ScenarioProfile"], bool] | None = None
    # Builds the Vietnamese goal text once goal_trigger returns True.
    goal_text: Callable[[dict], str] | None = None


def _trigger_heavy_rain(values: dict, profile: "ScenarioProfile") -> bool:
    return values["rain"] > FLOOD_RISK_HIGH_RAIN_MM


def _goal_text_heavy_rain(values: dict) -> str:
    return f"Ứng phó mưa lớn {values['rain']:.0f}mm/h và nguy cơ ngập úng tại Hà Nội (mô phỏng tự động)"


def _trigger_air_pollution(values: dict, profile: "ScenarioProfile") -> bool:
    return values["aqi"] > AQI_POLLUTION_THRESHOLD


def _goal_text_air_pollution(values: dict) -> str:
    return f"Ứng phó ô nhiễm không khí AQI {values['aqi']:.0f} tại Hà Nội (mô phỏng tự động)"


def _trigger_heatwave(values: dict, profile: "ScenarioProfile") -> bool:
    return values["temperature"] > HEATWAVE_TEMP_THRESHOLD_C


def _goal_text_heatwave(values: dict) -> str:
    return f"Ứng phó nắng nóng gay gắt {values['temperature']:.0f}°C và nguy cơ sốc nhiệt tại Hà Nội (mô phỏng tự động)"


def _trigger_major_event(values: dict, profile: "ScenarioProfile") -> bool:
    # No numeric "crowd density" reading exists in `values`, so this scenario
    # triggers probabilistically at the same rate it generates a crowd Event
    # row in _persist(), rather than piggy-backing on rain/AQI (which this
    # scenario's own ranges barely move — a real crowd event isn't a weather
    # phenomenon).
    return random.random() < profile.event_chance


def _goal_text_major_event(values: dict) -> str:
    return "Tăng cường an ninh và phân luồng giao thông cho sự kiện đông người tại Hà Nội (mô phỏng tự động)"


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
        goal_trigger=_trigger_heavy_rain,
        goal_text=_goal_text_heavy_rain,
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
        goal_trigger=_trigger_air_pollution,
        goal_text=_goal_text_air_pollution,
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
        goal_trigger=_trigger_heatwave,
        goal_text=_goal_text_heatwave,
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
        goal_trigger=_trigger_major_event,
        goal_text=_goal_text_major_event,
    ),
}
