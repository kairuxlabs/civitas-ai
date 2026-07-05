import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.agents.gemini_client import EMBED_DIM, embed_text
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION = "city_knowledge"


def _client() -> QdrantClient | None:
    if not settings.qdrant_url:
        return None
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


def _ensure_collection(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )


def _point_id(chunk: dict, i: int) -> int:
    """Stable point id derived from title + chunk_index via sha1, so re-runs
    in a fresh process (where Python's randomized hash() would otherwise
    differ) upsert onto the same Qdrant point instead of duplicating it."""
    key = f"{chunk.get('title', '')}::{chunk.get('chunk_index', i)}"
    return int(hashlib.sha1(key.encode()).hexdigest()[:16], 16)


def load_chunks(chunks: list[dict]) -> int:
    """chunks: metadata_builder.build_chunk_metadata() output. Returns the
    number of points actually upserted (chunks whose embedding failed are
    skipped, not retried). Any Qdrant network failure (unreachable/timeout/
    auth) is caught and logged, returning 0 rather than propagating, so this
    loader step fails in isolation."""
    client = _client()
    if client is None or not chunks:
        return 0

    points = []
    for i, chunk in enumerate(chunks):
        vector = embed_text(chunk["content"], task_type="RETRIEVAL_DOCUMENT")
        if vector is None:
            logger.warning(f"Skipping chunk {i} ('{chunk.get('title')}'): embedding failed")
            continue
        point_id = _point_id(chunk, i)
        points.append(PointStruct(id=point_id, vector=vector, payload=chunk))

    if not points:
        return 0

    try:
        _ensure_collection(client)
        client.upsert(collection_name=COLLECTION, points=points)
        return len(points)
    except Exception as e:
        logger.warning(f"Qdrant load_chunks failed: {e}")
        return 0
