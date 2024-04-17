from pydantic import BaseModel


class PartialCity(BaseModel):
    city_name: str
    lat: float
    lon: float


class City(BaseModel):
    city_name: str | None
    country: str
    lat: float
    lon: float
