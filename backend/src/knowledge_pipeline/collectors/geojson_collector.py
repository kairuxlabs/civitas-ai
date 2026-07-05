def build_district_geojson(boundary_elements: list[dict]) -> dict[str, dict]:
    """Map district name -> GeoJSON Feature, from raw Overpass boundary
    relation elements fetched with `out geom`. Prefers the Vietnamese name
    (`name:vi`) since that's what `districts.name` stores (see docker/postgres/init.sql)."""
    result: dict[str, dict] = {}
    for el in boundary_elements:
        tags = el.get("tags", {})
        name = tags.get("name:vi") or tags.get("name")
        if not name:
            continue

        coords = [
            [[pt["lon"], pt["lat"]] for pt in member["geometry"]]
            for member in el.get("members", [])
            if member.get("geometry")
        ]
        if not coords:
            continue

        result[name] = {
            "type": "Feature",
            "properties": {"name": name},
            "geometry": {"type": "MultiLineString", "coordinates": coords},
        }
    return result
