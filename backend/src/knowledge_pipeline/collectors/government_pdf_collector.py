import os

import aiohttp
import yaml

from src.knowledge_pipeline.collectors.base import BaseCollector
from src.knowledge_pipeline.parsers.pdf_parser import extract_pdf_text
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "pdf_sources.yaml")


def load_pdf_sources(config_path: str = CONFIG_PATH) -> list[dict]:
    if not os.path.exists(config_path):
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("sources") or []


class GovernmentPDFCollector(BaseCollector):
    """Reads config/pdf_sources.yaml (empty by default — no hardcoded
    government URLs ship with this codebase). Supports `local` (reads from
    disk) and `remote` (downloads) source entries via the same interface."""

    def __init__(self, config_path: str = CONFIG_PATH):
        self._config_path = config_path

    async def collect(self) -> list[dict]:
        sources = load_pdf_sources(self._config_path)
        if not sources:
            return []

        docs: list[dict] = []
        async with aiohttp.ClientSession() as http:
            for source in sources:
                try:
                    pdf_bytes = await self._read_source(http, source)
                    text = extract_pdf_text(pdf_bytes)
                    if text:
                        docs.append({
                            "title": source["name"],
                            "content": text,
                            "language": "vi",
                            "category": source.get("category", "government"),
                            "source": "GovernmentPDF",
                            "confidence": 0.8,
                        })
                except Exception as e:
                    logger.warning(f"Government PDF collector failed for {source.get('name')}: {e}")
        return docs

    @staticmethod
    async def _read_source(http: aiohttp.ClientSession, source: dict) -> bytes:
        if source["type"] == "local":
            with open(source["path"], "rb") as f:
                return f.read()
        async with http.get(source["url"]) as resp:
            return await resp.read()
