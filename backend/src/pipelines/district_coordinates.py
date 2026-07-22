# backend/src/pipelines/district_coordinates.py
"""Approximate real-world centroid (latitude, longitude) for each of Hanoi's
12 urban districts, used to fetch per-district weather/AQI readings instead
of a single city-wide point. District names must match the seed data in
docker/postgres/init.sql exactly."""

HANOI_CENTER = (21.0285, 105.8542)

DISTRICT_COORDINATES: dict[str, tuple[float, float]] = {
    "Hoàn Kiếm": (21.0285, 105.8542),
    "Ba Đình": (21.0355, 105.8342),
    "Đống Đa": (21.0151, 105.8281),
    "Hai Bà Trưng": (21.0021, 105.8544),
    "Hoàng Mai": (20.9764, 105.8531),
    "Thanh Xuân": (20.9954, 105.8069),
    "Cầu Giấy": (21.0333, 105.7975),
    "Long Biên": (21.0450, 105.8886),
    "Nam Từ Liêm": (21.0044, 105.7514),
    "Bắc Từ Liêm": (21.0708, 105.7522),
    "Tây Hồ": (21.0709, 105.8183),
    "Hà Đông": (20.9718, 105.7797),
}


def coordinates_for(district_name: str) -> tuple[float, float]:
    """Real centroid for a known district, falling back to the Hanoi city
    center for any unseeded/unknown district name."""
    return DISTRICT_COORDINATES.get(district_name, HANOI_CENTER)
