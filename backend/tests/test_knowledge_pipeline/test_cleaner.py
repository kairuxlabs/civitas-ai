from src.knowledge_pipeline.processors.cleaner import clean_text


def test_strips_html_tags():
    assert clean_text("<p>Hello <b>world</b></p>") == "Hello world"


def test_collapses_whitespace():
    assert clean_text("Hello   \n\n  world") == "Hello world"


def test_handles_empty_input():
    assert clean_text("") == ""
    assert clean_text(None) == ""
