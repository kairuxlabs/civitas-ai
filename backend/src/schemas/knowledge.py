from pydantic import BaseModel


class KnowledgeRelatedItem(BaseModel):
    name: str | None
    label: str | None
    relation: str | None
    related_name: str | None
    rel_source: str | None
    rel_confidence: float | None
    rel_created_at: str | None


class KnowledgeSummaryOut(BaseModel):
    configured: bool
    entities: int
    relations: int
    sample: list[KnowledgeRelatedItem]
