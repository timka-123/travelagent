from aiohttp import ClientSession

from utils.yandex_schedules.types.city import NearestCity


class YandexSchedule:
    """Simple and basic API wrapper for Yandex Schedule service. Required to get own API key from https://developer.tech.yandex.ru/services"""
    def __init__(self, api_key: str):
        """Init method for start `ClientSession`

        Args:
            api_key (str): API key of this service. You can get it from https://developer.tech.yandex.ru/services
        """
        self.session = ClientSession()
        self.session.headers.update({
            "Authorization": api_key
        })

        self.base_url = "https://api.rasp.yandex.net/v3.0"

    async def get_nearest_station(self, lat: float, lon: float) -> NearestCity:
        """Get nearest city nearest provied lat/lon

        Args:
            lat (float): Latitude of city
            lon (float): Longitude of city

        Returns:
            NearestCity: Nearest city type (more info about object there: https://yandex.ru/dev/rasp/doc/ru/reference/nearest-settlement#emails-detailed)
        """
        response = await self.session.get(
            url=f"{self.base_url}/nearest_settlement?lat={lat}&lon={lon}&format=json"
        )
        data = await response.json()
        return NearestCity(**data)

    async def get_schedule(
        self, 
        from_id: str,
        to_id: str
    ) -> dict:
        """Get methods to transfer from A to B on plane, train or other type on transport

        Args:
            from_id (str): ID of A in Yandex Schedule system
            to_id (str): ID of B in Yandex Schedule system

        Returns:
            dict: JSON object (more info there: https://yandex.ru/dev/rasp/doc/ru/reference/schedule-point-point#emails-detailed)
        """
        response = await self.session.get(
            url=f"{self.base_url}/search?from={from_id}&to={to_id}&format=json&limit=5"
        )
        return await response.json()
