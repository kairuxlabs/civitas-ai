import pytest

from src.knowledge_pipeline.collectors.base import BaseCollector


def test_cannot_instantiate_without_collect():
    with pytest.raises(TypeError):
        BaseCollector()


@pytest.mark.asyncio
async def test_subclass_implementing_collect_works():
    class DummyCollector(BaseCollector):
        async def collect(self) -> list[dict]:
            return [{"id": "1"}]

    result = await DummyCollector().collect()
    assert result == [{"id": "1"}]
