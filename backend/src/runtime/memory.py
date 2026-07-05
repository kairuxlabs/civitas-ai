# backend/src/runtime/memory.py
"""Memory runtime (spec_v2 §11, §14).

- Operational memory: RunStore (src/runtime/state.py)
- Knowledge memory: Qdrant when configured, keyword fallback over SOP docs
- Decision memory: Neo4j when configured, in-memory chain list fallback

External stores are strictly optional: any connection failure silently
degrades to the in-memory implementation.
"""
from datetime import datetime, timezone

from src.agents.knowledge_agent import _SOP_DOCS
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeMemory:
    """SOP / policy retrieval. Qdrant-backed when qdrant_url is set."""

    def search(self, query: str, k: int = 3) -> list[dict]:
        if settings.qdrant_url:
            try:
                return self._qdrant_search(query, k)
            except Exception as e:
                logger.warning(f"Qdrant unavailable, using keyword fallback: {e}")
        return self._keyword_search(query, k)

    def _keyword_search(self, query: str, k: int) -> list[dict]:
        q = query.lower()
        scored = []
        for doc in _SOP_DOCS:
            score = sum(1 for kw in doc["keywords"] if kw in q)
            if score > 0:
                scored.append({
                    "id": doc["id"], "title": doc["title"],
                    "content": doc["content"], "score": score,
                })
        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:k]

    def _qdrant_search(self, query: str, k: int) -> list[dict]:
        from qdrant_client import QdrantClient  # optional dependency

        from src.agents.gemini_client import embed_text

        vector = embed_text(query, task_type="RETRIEVAL_QUERY")
        if vector is None:
            raise RuntimeError("Gemini embedding unavailable")

        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)

        # Reranking is opt-in (requires an OpenRouter key). When disabled, this
        # path is byte-identical to the original: same limit, same order.
        use_rerank = bool(settings.openrouter_api_key)
        search_limit = max(k * 4, 20) if use_rerank else k
        hits = client.search(collection_name="cityos_sop", query_vector=vector, limit=search_limit)

        if use_rerank and hits:
            try:
                import asyncio

                from src.ai.reranker import rerank

                documents = [h.payload.get("content", "") for h in hits]
                order = asyncio.run(rerank(query, documents, top_k=k))
                reranked = [hits[i] for i in order if 0 <= i < len(hits)]
                if reranked:
                    hits = reranked
                else:
                    hits = hits[:k]
            except Exception as e:
                logger.warning(f"Rerank unavailable, using Qdrant order: {e}")
                hits = hits[:k]
        else:
            hits = hits[:k]

        return [
            {
                "id": h.payload.get("doc_id", h.id),
                "title": h.payload.get("title", ""),
                "content": h.payload.get("content", ""),
                "score": h.score,
            }
            for h in hits
        ]


class DecisionMemory:
    """Incident → Decision → Workflow → Outcome chains. Neo4j-backed when configured."""

    def __init__(self):
        self._chains: list[dict] = []

    def store_chain(self, incident: dict, decision: dict, workflow: dict, outcome: str) -> None:
        chain = {
            "incident": incident,
            "decision": decision,
            "workflow": workflow,
            "outcome": outcome,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._chains.append(chain)
        if settings.neo4j_uri:
            try:
                self._neo4j_store(chain)
            except Exception as e:
                logger.warning(f"Neo4j unavailable, chain kept in memory only: {e}")

    def recent(self, n: int = 10) -> list[dict]:
        return list(reversed(self._chains))[:n]

    def _neo4j_store(self, chain: dict) -> None:
        import json

        from neo4j import GraphDatabase  # optional dependency
        driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        with driver.session() as session:
            session.run(
                """
                CREATE (i:Incident {data: $incident, ts: $ts})
                CREATE (d:Decision {data: $decision})
                CREATE (w:Workflow {data: $workflow})
                CREATE (o:Outcome {value: $outcome})
                CREATE (i)-[:LED_TO]->(d)-[:EXECUTED_AS]->(w)-[:RESULTED_IN]->(o)
                """,
                incident=json.dumps(chain["incident"]),
                decision=json.dumps(chain["decision"]),
                workflow=json.dumps(chain["workflow"]),
                outcome=chain["outcome"],
                ts=chain["ts"],
            )
        driver.close()


knowledge_memory = KnowledgeMemory()
decision_memory = DecisionMemory()
