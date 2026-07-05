from src.knowledge_pipeline.collectors.geojson_collector import build_district_geojson


def test_builds_feature_for_named_boundary_with_geometry():
    elements = [{
        "type": "relation", "id": 1,
        "tags": {"name": "Ba Dinh", "name:vi": "Ba Đình"},
        "members": [{"type": "way", "geometry": [{"lat": 21.03, "lon": 105.83}, {"lat": 21.04, "lon": 105.84}]}],
    }]
    result = build_district_geojson(elements)
    assert "Ba Đình" in result
    feature = result["Ba Đình"]
    assert feature["type"] == "Feature"
    assert feature["properties"]["name"] == "Ba Đình"
    assert feature["geometry"]["coordinates"] == [[[105.83, 21.03], [105.84, 21.04]]]


def test_skips_boundary_without_name():
    elements = [{"type": "relation", "id": 2, "tags": {}, "members": [{"geometry": [{"lat": 1, "lon": 2}]}]}]
    assert build_district_geojson(elements) == {}


def test_skips_boundary_without_members():
    elements = [{"type": "relation", "id": 3, "tags": {"name": "Empty"}, "members": []}]
    assert build_district_geojson(elements) == {}
