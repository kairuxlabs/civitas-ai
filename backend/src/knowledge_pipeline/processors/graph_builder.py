import json

LABEL_BY_TYPE: dict[str, str] = {
    "hospital": "Hospital", "fire_station": "FireStation", "police": "PoliceStation",
    "school": "School", "road": "Road", "bus_stop": "BusStop", "park": "Park",
    "river": "River", "lake": "Lake", "building": "Building",
}


def to_node_row(entity: dict) -> dict:
    """Flatten a CityEntity into a Neo4j-safe property map (no nested
    objects — Neo4j node properties must be primitives or arrays of
    primitives)."""
    geometry = entity.get("geometry") or {}
    metadata = entity.get("metadata") or {}
    capacity = entity.get("capacity")
    return {
        "id": entity["id"],
        "name": entity["name"],
        "display_name": entity.get("display_name", entity["name"]),
        "lat": geometry.get("lat"),
        "lon": geometry.get("lon"),
        "district": entity.get("district", ""),
        "tags": entity.get("tags", []),
        "importance": entity.get("importance", 0),
        "criticality": entity.get("criticality", "low"),
        "status": entity.get("status", "normal"),
        "confidence": entity.get("confidence", 1.0),
        "capacity": json.dumps(capacity) if capacity is not None else None,
        "source": metadata.get("source", ""),
        "updated_at": metadata.get("updated_at", ""),
        "wikidata_label": metadata.get("wikidata_label"),
        "wikidata_instance_of": metadata.get("wikidata_instance_of"),
    }


def _group_by_type(entities: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for entity in entities:
        grouped.setdefault(entity["type"], []).append(entity)
    return grouped


def build_entity_graph(entities: list[dict], loader) -> dict[str, int]:
    """Upsert all CityEntities as nodes, grouped by type. Returns the number
    of rows upserted per Neo4j label."""
    counts: dict[str, int] = {}
    for entity_type, rows in _group_by_type(entities).items():
        label = LABEL_BY_TYPE.get(entity_type, entity_type.capitalize())
        node_rows = [to_node_row(e) for e in rows]
        counts[label] = loader.upsert_nodes(label, node_rows)
    return counts


def build_relation_graph(relations: list[dict], loader) -> int:
    """relations: [{"from_type", "from_name", "rel", "to_type", "to_name"}],
    as produced by bootstrap.py from entity_extractor output. Types that
    don't map to a known OSM entity label (e.g. "flood", "emergency") fall
    back to a generic "Concept" node."""
    count = 0
    for rel in relations:
        from_label = LABEL_BY_TYPE.get(rel["from_type"].lower(), "Concept")
        to_label = LABEL_BY_TYPE.get(rel["to_type"].lower(), "Concept")
        ok = loader.merge_relation_by_name(from_label, rel["from_name"], rel["rel"], to_label, rel["to_name"])
        if ok:
            count += 1
    return count
