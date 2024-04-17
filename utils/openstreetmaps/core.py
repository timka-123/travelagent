from json import JSONDecodeError
from typing import Optional

from aiohttp import ClientSession

from .types import City, PartialCity


class OpenStreetMapsClient:
    def __init__(self):
        self._session = ClientSession()
        self._base_url = "https://nominatim.openstreetmap.org"

    def _get_name(self, data: dict) -> Optional[str]:
        name = data.get("city")
        if not name and data.get("town"):
            name = data.get("town")
        if not name and data.get("village"):
            name = data.get("village")
        return name

    async def get_location_info(self, lat: float, lon: float) -> Optional[City]:
        response = await self._session.get(
            url=self._base_url + f"/reverse?format=json&lat={lat}&lon={lon}"
        )
        data = await response.json()
        try:
            data = data['address']
            return City(
                city_name=self._get_name(data),
                country=data.get("country"),
                lat=lat,
                lon=lon
            )
        except KeyError:
            return

    async def get_city(self, city_name: str) -> Optional[PartialCity]:
        response = await self._session.get(
            url=self._base_url + f"/search?format=json&city={city_name}"
        )
        try:
            data = await response.json()
            for item in data:
                if item['type'] in ['town', 'city', 'village']:
                    return PartialCity(
                        city_name=item['name'],
                        lat=item['boundingbox'][0],
                        lon=item['boundingbox'][2]
                    )
            return
        except JSONDecodeError:
            return

    async def check_if_country_exists(self, country_name: str) -> bool:
        response = await self._session.get(
            url=self._base_url + f"/search?format=json&country={country_name}"
        )
        try:
            data = await response.json()
            return True
        except JSONDecodeError:
            return False
