from pydantic import BaseModel


class DistrictOut(BaseModel):
    id: int
    city_id: str
    name: str
    geojson: dict | None = None

    model_config = {"from_attributes": True}
