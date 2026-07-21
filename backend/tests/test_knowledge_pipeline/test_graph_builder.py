from src.knowledge_pipeline.processors.graph_builder import (
    to_node_row, build_entity_graph, build_relation_graph, LABEL_BY_TYPE,
)


class FakeLoader:
    def __init__(self):
        self.node_calls = []
        self.relation_calls = []

    def upsert_nodes(self, label, rows):
        self.node_calls.append((label, rows))
        return len(rows)

    def merge_relation_by_name(self, from_label, from_name, rel_type, to_label, to_name,
                                source=None, confidence=None, created_at=None):
        self.relation_calls.append((from_label, from_name, rel_type, to_label, to_name, source, confidence, created_at))
        return True


def test_to_node_row_flattens_geometry_metadata_and_capacity():
    entity = {
        "id": "hospital_1", "name": "Bach Mai", "display_name": "Bệnh viện Bạch Mai",
        "geometry": {"type": "Point", "lat": 21.0, "lon": 105.8},
        "district": "Hai Ba Trung", "tags": ["healthcare"],
        "importance": 95, "criticality": "critical", "status": "normal", "confidence": 1.0,
        "capacity": {"beds": 1200},
        "metadata": {"source": "OpenStreetMap", "updated_at": "2026-07-05"},
    }
    row = to_node_row(entity)
    assert row["lat"] == 21.0 and row["lon"] == 105.8
    assert row["capacity"] == '{"beds": 1200}'
    assert row["source"] == "OpenStreetMap"
    assert "geometry" not in row and "metadata" not in row
    assert row["wikidata_label"] is None
    assert row["wikidata_instance_of"] is None


def test_to_node_row_carries_wikidata_enrichment_fields_when_present():
    entity = {
        "id": "hospital_1", "name": "Bach Mai", "display_name": "Bệnh viện Bạch Mai",
        "geometry": {"type": "Point", "lat": 21.0, "lon": 105.8},
        "district": "Hai Ba Trung", "tags": ["healthcare"],
        "importance": 95, "criticality": "critical", "status": "normal", "confidence": 0.9,
        "capacity": None,
        "metadata": {
            "source": "OpenStreetMap", "updated_at": "2026-07-05",
            "wikidata_qid": "Q194189",
            "wikidata_label": "Bach Mai Hospital",
            "wikidata_instance_of": "hospital",
        },
    }
    row = to_node_row(entity)
    assert row["wikidata_label"] == "Bach Mai Hospital"
    assert row["wikidata_instance_of"] == "hospital"


def test_to_node_row_carries_enriched_by_and_enriched_at_when_present():
    entity = {
        "id": "hospital_1", "name": "Bach Mai", "display_name": "Bệnh viện Bạch Mai",
        "geometry": {"type": "Point", "lat": 21.0, "lon": 105.8},
        "district": "Hai Ba Trung", "tags": ["healthcare"],
        "importance": 95, "criticality": "critical", "status": "normal", "confidence": 0.9,
        "capacity": None,
        "metadata": {
            "source": "OpenStreetMap", "updated_at": "2026-07-05",
            "wikidata_label": "Bach Mai Hospital", "wikidata_instance_of": "hospital",
            "enriched_by": "Wikidata", "enriched_at": "2026-07-21T09:00:00+00:00",
        },
    }
    row = to_node_row(entity)
    assert row["enriched_by"] == "Wikidata"
    assert row["enriched_at"] == "2026-07-21T09:00:00+00:00"
    assert row["source"] == "OpenStreetMap"
    assert row["updated_at"] == "2026-07-05"


def test_to_node_row_defaults_enriched_fields_to_none_when_absent():
    entity = {
        "id": "hospital_1", "name": "Bach Mai", "display_name": "Bệnh viện Bạch Mai",
        "geometry": {}, "district": "", "tags": [], "importance": 0,
        "criticality": "low", "status": "normal", "confidence": 1.0, "capacity": None,
        "metadata": {"source": "OpenStreetMap", "updated_at": "2026-07-05"},
    }
    row = to_node_row(entity)
    assert row["enriched_by"] is None
    assert row["enriched_at"] is None


def test_build_entity_graph_groups_by_type_and_upserts_per_label():
    entities = [
        {"id": "hospital_1", "type": "hospital", "name": "A", "geometry": {}, "metadata": {}},
        {"id": "school_1", "type": "school", "name": "B", "geometry": {}, "metadata": {}},
    ]
    loader = FakeLoader()
    counts = build_entity_graph(entities, loader)
    assert counts == {"Hospital": 1, "School": 1}
    assert len(loader.node_calls) == 2


def test_build_relation_graph_uses_label_by_type_with_concept_fallback():
    relations = [
        {"from_type": "hospital", "from_name": "Bach Mai", "rel": "IMPACTS", "to_type": "flood", "to_name": "Flood"},
    ]
    loader = FakeLoader()
    count = build_relation_graph(relations, loader)
    assert count == 1
    from_label, from_name, rel, to_label, to_name, source, confidence, created_at = loader.relation_calls[0]
    assert from_label == "Hospital"
    assert to_label == "Concept"  # "flood" is not in LABEL_BY_TYPE
    assert rel == "IMPACTS"
    assert source is None  # no "source" key on this relation dict
    assert confidence is None  # not computed by the entity extractor today
    assert created_at  # non-empty ISO timestamp


def test_build_relation_graph_passes_through_source_when_present():
    relations = [
        {"from_type": "hospital", "from_name": "Bach Mai", "rel": "IMPACTS", "to_type": "flood",
         "to_name": "Flood", "source": "Wikipedia"},
    ]
    loader = FakeLoader()
    build_relation_graph(relations, loader)
    _, _, _, _, _, source, _, _ = loader.relation_calls[0]
    assert source == "Wikipedia"
