from datetime import datetime, timezone


def build_chunk_metadata(chunk: str, doc: dict, chunk_index: int, city: str = "Hanoi") -> dict:
    """The exact payload shape stored as a Qdrant point's payload."""
    return {
        "content": chunk,
        "title": doc.get("title", ""),
        "category": doc.get("category", "general"),
        "language": doc.get("language", "en"),
        "source": doc.get("source", "unknown"),
        "city": city,
        "chunk_index": chunk_index,
        "confidence": doc.get("confidence", 0.85),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
