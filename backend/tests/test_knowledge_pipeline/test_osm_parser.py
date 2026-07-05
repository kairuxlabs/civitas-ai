from src.knowledge_pipeline.parsers.osm_parser import parse_osm_elements

CONFIG = {"importance": 95, "criticality": "critical", "limit": None}


def test_parses_node_element_with_coordinates():
    elements = [{
        "type": "node", "id": 123, "lat": 21.0008, "lon": 105.8412,
        "tags": {"name": "Bach Mai Hospital", "addr:district": "Hai Ba Trung"},
    }]
    result = parse_osm_elements(elements, "hospital", CONFIG)
    assert len(result) == 1
    entity = result[0]
    assert entity["id"] == "hospital_123"
    assert entity["type"] == "hospital"
    assert entity["name"] == "Bach Mai Hospital"
    assert entity["geometry"] == {"type": "Point", "lat": 21.0008, "lon": 105.8412}
    assert entity["district"] == "Hai Ba Trung"
    assert entity["importance"] == 95
    assert entity["criticality"] == "critical"
    assert entity["status"] == "normal"
    assert entity["confidence"] == 1.0
    assert entity["capacity"] is None
    assert entity["metadata"]["source"] == "OpenStreetMap"
    assert entity["metadata"]["osm_id"] == 123


def test_parses_way_element_using_center():
    elements = [{
        "type": "way", "id": 456, "center": {"lat": 21.03, "lon": 105.85}, "tags": {},
    }]
    result = parse_osm_elements(elements, "school", CONFIG)
    assert result[0]["geometry"] == {"type": "Point", "lat": 21.03, "lon": 105.85}
    assert result[0]["name"] == "school_456"


def test_skips_element_without_coordinates():
    elements = [{"type": "way", "id": 789, "tags": {"name": "No Geometry"}}]
    result = parse_osm_elements(elements, "hospital", CONFIG)
    assert result == []


def test_captures_wikidata_qid_when_present():
    elements = [{"type": "node", "id": 1, "lat": 21.0, "lon": 105.8, "tags": {"wikidata": "Q123"}}]
    result = parse_osm_elements(elements, "hospital", CONFIG)
    assert result[0]["metadata"]["wikidata_qid"] == "Q123"


def test_respects_limit():
    elements = [
        {"type": "node", "id": i, "lat": 21.0, "lon": 105.8, "tags": {}}
        for i in range(5)
    ]
    result = parse_osm_elements(elements, "building", {**CONFIG, "limit": 2})
    assert len(result) == 2
