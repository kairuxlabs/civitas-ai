import aiohttp

from src.knowledge_pipeline.collectors.base import BaseCollector
from src.utils.logger import get_logger

logger = get_logger(__name__)

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"


def build_sparql_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in qids)
    return (
        f"SELECT ?item ?itemLabel ?instanceOfLabel WHERE {{ "
        f"VALUES ?item {{ {values} }} "
        f"OPTIONAL {{ ?item wdt:P31 ?instanceOf. }} "
        f'SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,vi". }} }}'
    )


class WikidataCollector(BaseCollector):
    """Best-effort enrichment of OSM entities that carry a `wikidata` tag.
    Entities without the tag are left untouched. Mutates matched entities
    in place (see class docstring in the design spec)."""

    def __init__(self, entities: list[dict]):
        self._entities = entities

    async def collect(self) -> list[dict]:
        by_qid = {
            e["metadata"]["wikidata_qid"]: e
            for e in self._entities
            if e.get("metadata", {}).get("wikidata_qid")
        }
        if not by_qid:
            return []

        try:
            query = build_sparql_query(list(by_qid))
            async with aiohttp.ClientSession() as http:
                async with http.get(
                    WIKIDATA_SPARQL_URL,
                    params={"query": query, "format": "json"},
                    headers={"Accept": "application/sparql-results+json"},
                ) as resp:
                    data = await resp.json()
        except Exception as e:
            logger.warning(f"Wikidata enrichment failed: {e}")
            return []

        enriched = []
        for row in data.get("results", {}).get("bindings", []):
            qid = row.get("item", {}).get("value", "").rsplit("/", 1)[-1]
            entity = by_qid.get(qid)
            if not entity:
                continue
            entity["metadata"]["wikidata_label"] = row.get("itemLabel", {}).get("value")
            entity["metadata"]["wikidata_instance_of"] = row.get("instanceOfLabel", {}).get("value")
            entity["confidence"] = 0.9
            enriched.append(entity)
        return enriched
