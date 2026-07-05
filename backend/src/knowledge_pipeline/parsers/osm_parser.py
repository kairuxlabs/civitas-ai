from datetime import date


def parse_osm_elements(elements: list[dict], entity_type: str, config: dict) -> list[dict]:
    """Turn raw Overpass `elements` (all fetched for one entity_type/config)
    into CityEntity dicts. Elements without resolvable coordinates are
    dropped (way/relation elements need `out center` in the Overpass query)."""
    entities: list[dict] = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue

        name = tags.get("name") or f"{entity_type}_{el['id']}"
        metadata = {
            "source": "OpenStreetMap",
            "updated_at": date.today().isoformat(),
            "version": "1.0",
            "osm_id": el["id"],
        }
        if tags.get("wikidata"):
            metadata["wikidata_qid"] = tags["wikidata"]

        entities.append({
            "id": f"{entity_type}_{el['id']}",
            "type": entity_type,
            "name": name,
            "display_name": tags.get("name:vi", name),
            "geometry": {"type": "Point", "lat": lat, "lon": lon},
            "district": tags.get("addr:district", ""),
            "tags": [entity_type],
            "importance": config["importance"],
            "criticality": config["criticality"],
            "status": "normal",
            "confidence": 1.0,
            "capacity": None,
            "metadata": metadata,
        })

    limit = config.get("limit")
    return entities[:limit] if limit else entities
