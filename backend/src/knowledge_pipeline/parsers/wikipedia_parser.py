import re


def clean_wikitext(raw_extract: str) -> str:
    return re.sub(r"\n{2,}", "\n\n", raw_extract or "").strip()


def parse_wikipedia_page(payload: dict, category: str) -> dict | None:
    """payload: one entry from MediaWiki API's `query.pages` dict."""
    title = payload.get("title")
    extract = payload.get("extract")
    if not title or not extract:
        return None
    return {
        "title": title,
        "content": clean_wikitext(extract),
        "language": "en",
        "category": category,
        "source": "Wikipedia",
        "confidence": 0.85,
    }
