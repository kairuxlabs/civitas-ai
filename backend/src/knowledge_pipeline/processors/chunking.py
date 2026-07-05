def chunk_text(text: str, max_chars: int = 3000, overlap: int = 200) -> list[str]:
    """Sentence-aware splitter: ~max_chars per chunk, with `overlap` chars
    of trailing context carried into the next chunk so entity mentions
    near a chunk boundary aren't lost entirely."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}." if current else f"{sentence}."
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = current[-overlap:] + " " + sentence + "."
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks
