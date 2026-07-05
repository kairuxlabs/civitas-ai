import pytest
from unittest.mock import AsyncMock, patch

from src.knowledge_pipeline.collectors.government_pdf_collector import (
    GovernmentPDFCollector, load_pdf_sources,
)


def test_load_pdf_sources_returns_empty_list_for_default_config(tmp_path):
    config = tmp_path / "pdf_sources.yaml"
    config.write_text("sources: []\n", encoding="utf-8")
    assert load_pdf_sources(str(config)) == []


def test_load_pdf_sources_parses_entries(tmp_path):
    config = tmp_path / "pdf_sources.yaml"
    config.write_text(
        "sources:\n  - name: Test SOP\n    type: local\n    path: x.pdf\n    category: disaster\n",
        encoding="utf-8",
    )
    sources = load_pdf_sources(str(config))
    assert sources == [{"name": "Test SOP", "type": "local", "path": "x.pdf", "category": "disaster"}]


@pytest.mark.asyncio
async def test_collect_returns_empty_list_when_no_sources_configured(tmp_path):
    config = tmp_path / "pdf_sources.yaml"
    config.write_text("sources: []\n", encoding="utf-8")
    docs = await GovernmentPDFCollector(config_path=str(config)).collect()
    assert docs == []


@pytest.mark.asyncio
async def test_collect_reads_local_pdf_source(tmp_path, monkeypatch):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"fake-pdf-bytes")
    config = tmp_path / "pdf_sources.yaml"
    config.write_text(
        f"sources:\n  - name: Test SOP\n    type: local\n    path: {pdf_path}\n    category: disaster\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "src.knowledge_pipeline.collectors.government_pdf_collector.extract_pdf_text",
        lambda pdf_bytes: "Extracted SOP text.",
    )

    docs = await GovernmentPDFCollector(config_path=str(config)).collect()
    assert len(docs) == 1
    assert docs[0]["title"] == "Test SOP"
    assert docs[0]["content"] == "Extracted SOP text."
    assert docs[0]["category"] == "disaster"
    assert docs[0]["source"] == "GovernmentPDF"
    assert docs[0]["confidence"] == 0.8
