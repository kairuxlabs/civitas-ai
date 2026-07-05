from src.knowledge_pipeline.parsers.pdf_parser import extract_pdf_text


def test_joins_text_from_all_pages(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self._text = text
        def extract_text(self):
            return self._text

    class FakeReader:
        def __init__(self, _bytes):
            self.pages = [FakePage("Page one."), FakePage("Page two.")]

    monkeypatch.setattr("src.knowledge_pipeline.parsers.pdf_parser.PdfReader", FakeReader)
    assert extract_pdf_text(b"fake-pdf-bytes") == "Page one.\nPage two."


def test_handles_page_with_no_extractable_text(monkeypatch):
    class FakePage:
        def extract_text(self):
            return None

    class FakeReader:
        def __init__(self, _bytes):
            self.pages = [FakePage()]

    monkeypatch.setattr("src.knowledge_pipeline.parsers.pdf_parser.PdfReader", FakeReader)
    assert extract_pdf_text(b"fake-pdf-bytes") == ""
