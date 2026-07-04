"""Per-type Overpass tag + CityEntity defaults for the OSM collector."""

ENTITY_TYPES: dict[str, dict] = {
    "hospital": {"tag": "amenity", "value": "hospital", "limit": None, "importance": 95, "criticality": "critical"},
    "fire_station": {"tag": "amenity", "value": "fire_station", "limit": None, "importance": 95, "criticality": "critical"},
    "police": {"tag": "amenity", "value": "police", "limit": None, "importance": 90, "criticality": "high"},
    "school": {"tag": "amenity", "value": "school", "limit": None, "importance": 70, "criticality": "high"},
    "bus_stop": {"tag": "highway", "value": "bus_stop", "limit": 300, "importance": 60, "criticality": "medium"},
    "park": {"tag": "leisure", "value": "park", "limit": None, "importance": 50, "criticality": "medium"},
    "building": {"tag": "building", "value": "yes", "limit": 500, "importance": 20, "criticality": "low"},
}

ROAD_TYPES: dict = {
    "tag": "highway",
    "values": ["motorway", "primary", "secondary", "tertiary"],
    "limit": 2000,
    "importance": 90,
    "criticality": "high",
}

NAMED_RIVERS: list[str] = ["Sông Hồng", "Sông Tô Lịch", "Hồ Tây", "Hồ Hoàn Kiếm"]

RIVER_CONFIG: dict = {"importance": 60, "criticality": "medium"}

# (south, west, north, east) — bounding box covering the 12 Hanoi districts
HANOI_BBOX: tuple[float, float, float, float] = (20.95, 105.75, 21.15, 105.95)
