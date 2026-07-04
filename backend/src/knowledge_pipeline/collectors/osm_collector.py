import aiohttp

from src.knowledge_pipeline.collectors.base import BaseCollector
from src.knowledge_pipeline.config.entity_types import (
    ENTITY_TYPES, HANOI_BBOX, NAMED_RIVERS, RIVER_CONFIG, ROAD_TYPES,
)
from src.knowledge_pipeline.parsers.osm_parser import parse_osm_elements
from src.utils.logger import get_logger

logger = get_logger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _bbox_str() -> str:
    south, west, north, east = HANOI_BBOX
    return f"{south},{west},{north},{east}"


def build_tag_query(tag: str, value: str) -> str:
    bbox = _bbox_str()
    return (
        f'[out:json][timeout:60];'
        f'(node["{tag}"="{value}"]({bbox});way["{tag}"="{value}"]({bbox}););'
        f'out center;'
    )


def build_river_query(name: str) -> str:
    return f'[out:json][timeout:60];way["waterway"]["name"="{name}"]({_bbox_str()});out center;'


def build_boundary_query() -> str:
    return (
        f'[out:json][timeout:60];'
        f'relation["admin_level"="8"]["boundary"="administrative"]({_bbox_str()});'
        f'out geom;'
    )


class OSMCollector(BaseCollector):
    async def collect(self) -> list[dict]:
        entities: list[dict] = []
        async with aiohttp.ClientSession() as http:
            for entity_type, config in ENTITY_TYPES.items():
                elements = await self._query(http, build_tag_query(config["tag"], config["value"]), f"entity/{entity_type}")
                entities.extend(parse_osm_elements(elements, entity_type, config))

            for value in ROAD_TYPES["values"]:
                elements = await self._query(http, build_tag_query(ROAD_TYPES["tag"], value), f"road/{value}")
                entities.extend(parse_osm_elements(elements, "road", ROAD_TYPES))

            for name in NAMED_RIVERS:
                elements = await self._query(http, build_river_query(name), f"river/{name}")
                entities.extend(parse_osm_elements(elements, "river", RIVER_CONFIG))

        return entities

    async def collect_district_boundaries(self) -> list[dict]:
        async with aiohttp.ClientSession() as http:
            return await self._query(http, build_boundary_query(), "district_boundaries")

    @staticmethod
    async def _query(http: aiohttp.ClientSession, query: str, label: str) -> list[dict]:
        try:
            async with http.post(OVERPASS_URL, data={"data": query}) as resp:
                data = await resp.json()
            return data.get("elements", [])
        except Exception as e:
            logger.warning(f"OSM collector failed for {label}: {e}")
            return []
