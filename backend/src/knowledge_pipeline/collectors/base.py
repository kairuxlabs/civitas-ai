from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """A collector fetches raw data from one open-data source and returns
    a list of normalized dicts (CityEntity shape for geo sources, doc shape
    for text sources). Every concrete collector must isolate its own
    failures — collect() should not raise for a single bad element/page."""

    @abstractmethod
    async def collect(self) -> list[dict]:
        ...
