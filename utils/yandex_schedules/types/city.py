from typing import Literal

from pydantic import BaseModel


class NearestCity(BaseModel):
    distance: float
    code: str
    title: str
    popular_title: str
    short_title: str
    lat: float
    lon: float
    type: Literal['station', 'settlement']
