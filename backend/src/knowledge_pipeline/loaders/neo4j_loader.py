from neo4j import GraphDatabase

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Neo4jLoader:
    """Thin, idempotent Cypher executor. No-ops when Neo4j isn't configured
    (settings.neo4j_uri empty) — matches the fallback convention already
    used by src/runtime/memory.py's DecisionMemory."""

    def __init__(self):
        self._driver = None
        if settings.neo4j_uri:
            try:
                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j driver: {e}")
                self._driver = None

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def upsert_nodes(self, label: str, rows: list[dict]) -> int:
        """Bulk MERGE by `id`. `rows` must be flat dicts (no nested objects) —
        see graph_builder.to_node_row for the CityEntity -> row conversion."""
        if not self._driver or not rows:
            return 0
        query = f"UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) SET n += row"
        try:
            with self._driver.session() as session:
                session.run(query, rows=rows)
            return len(rows)
        except Exception as e:
            logger.warning(f"Neo4j upsert_nodes({label}) failed: {e}")
            return 0

    def merge_relation_by_name(
        self, from_label: str, from_name: str, rel_type: str, to_label: str, to_name: str
    ) -> bool:
        """MERGEs both endpoints by `name` (creating lightweight nodes if they
        don't already exist) and the relationship between them. Used for
        entity-extraction-derived relations, which reference concepts by
        name, not by OSM id."""
        if not self._driver:
            return False
        query = (
            f"MERGE (a:{from_label} {{name: $from_name}}) "
            f"MERGE (b:{to_label} {{name: $to_name}}) "
            f"MERGE (a)-[:{rel_type}]->(b)"
        )
        try:
            with self._driver.session() as session:
                session.run(query, from_name=from_name, to_name=to_name)
            return True
        except Exception as e:
            logger.warning(f"Neo4j merge_relation_by_name failed: {e}")
            return False

    def find_related(self, keywords: list[str], limit: int = 5) -> list[dict]:
        """Read-side counterpart to upsert_nodes/merge_relation_by_name. Finds
        nodes whose name or display_name contains any of the given keywords
        (case-insensitive), along with one hop of their relations. No-ops
        (returns []) when Neo4j isn't configured, the driver failed to
        initialize, or keywords is empty."""
        if not self._driver or not keywords:
            return []
        query = (
            "UNWIND $keywords AS kw "
            "MATCH (n) "
            "WHERE toLower(n.name) CONTAINS toLower(kw) OR toLower(n.display_name) CONTAINS toLower(kw) "
            "OPTIONAL MATCH (n)-[r]-(m) "
            "RETURN DISTINCT n.name AS name, labels(n)[0] AS label, type(r) AS relation, m.name AS related_name "
            "LIMIT $limit"
        )
        try:
            with self._driver.session() as session:
                result = session.run(query, keywords=keywords, limit=limit)
                return [
                    {
                        "name": row["name"],
                        "label": row["label"],
                        "relation": row["relation"],
                        "related_name": row["related_name"],
                    }
                    for row in result
                ]
        except Exception as e:
            logger.warning(f"Neo4j find_related failed: {e}")
            return []
