from datetime import date, datetime, timedelta
from typing import Any
from aiohttp import ClientSession

from utils.yandex_schedules.types.city import NearestCity
from googletrans import Translator


class YandexSchedule:
    """Simple and basic API wrapper for Yandex Schedule service. Required to get own API key from https://developer.tech.yandex.ru/services"""
    def __init__(self, api_key: str):
        """Init method for start `ClientSession`

        Args:
            api_key (str): API key of this service. You can get it from https://developer.tech.yandex.ru/services
        """
        self.session = ClientSession()
        self.session.headers.update({
            "Authorization": api_key,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        })
        self.translator = Translator()

        self.base_url = "https://api.rasp.yandex.net/v3.0"
        self.private_api_url = "https://rasp.yandex.ru/api/batch"

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
    
    async def get_slug_name(self, name: str) -> str:
        response = await self.session.get(
            url=f"https://suggests.rasp.yandex.net/by_t_type?format=old&part={name}"
        )
        resp = await response.json()
        return resp[1][0][3], resp[1][0][0]
    
    async def get_context(self, from_name: str, to_name: str) -> Any:
        from_slug, from_code = await self.get_slug_name(from_name)
        to_slug, to_code = await self.get_slug_name(to_name)
        data = {
            "methods": [{
                "method": "parseContext",
                "params": {
                    "tld": "ru",
                    "language": "ru",
                    "transportType": "all",
                    "fromSlug": from_slug,
                    "fromKey": from_code,
                    "fromTitle": from_name,
                    "toSlug": to_slug,
                    "toKey": to_code,
                    "toTitle": to_name
                }
            }]
        }
        response = await self.session.post(
            url=self.private_api_url,
            json=data
        )
        resp_data = await response.json()
        return resp_data[0]['data']
    
    async def get_trains(self, from_name: str, to_name: str, date_of_dep: date) -> list[dict]:
        from_slug, from_code = await self.get_slug_name(from_name)
        to_slug, to_code = await self.get_slug_name(to_name)
        dep_datetime = datetime(
            year=date_of_dep.year, month=date_of_dep.month, day=date_of_dep.day, hour=0, second=0, minute=0
        )
        data = {
            "methods": [
                {
                    "method": "trainTariffs2",
                    "params": {
                        "transportType": "train",
                        "pointFrom": from_code,
                        "pointTo": to_code,
                        "now": int(datetime.now().timestamp() * 1000),
                        "language": "ru",
                        "nationalVersion": "ru",
                        "flags": {
                            "INTMONETIZATION-1394-2": "enabled",
                            "__everlastingStationTouchExperiment": True,
                            "__everlastingThreadTouchExperiment": False,
                            "__experiment": False,
                            "__filledSchemaRequirements": False,
                            "__mirCashbackBanner": False,
                            "__notCanonicalThreadUid": False,
                            "__ridesharingPartnersDisabled": True,
                            "__showFlagsInConsole": False,
                            "__ufsTesting": False,
                            "__webvisor": False,
                            "__yabusOfflineLabel": 1
                        },
                        "poll": False,
                        "environmentType": "client",
                        "startTime": dep_datetime.isoformat() + "Z",
                        "endTime": (dep_datetime + timedelta(days=1)).isoformat() + "Z"
                    }
                }
            ]
        }
        response = await self.session.post(
            url=self.private_api_url,
            json=data
        )
        resp_data = await response.json()
        items = []
        for segment in resp_data['data'][0]['data']['trainTariffs']['segments']:
            tarifs = []
            for tarif_service_name, tarif_desc in segment['tariffs']['classes'].items():
                tarifs.append([tarif_desc['price']['value'], f"https://travel.yandex.ru/trains{tarif_desc['trainOrderUrl']}"])
            tarifs = sorted(tarifs, key=lambda x: x[0])
            items.append({
                "title": f"{segment['title']} - {segment['number']} - {tarifs[0][0]} руб.",
                "link": tarifs[0][1]
            })
        return items

    async def get_avia(self, from_name: str, to_name: str) -> list[str]:
        from_city = await self.get_nearest_station(from_name)
        to_city = await self.get_nearest_station(to_name)
        context = await self.get_context(from_name, to_name)
        data = {
            "methods": [{
                "method": "startPlaneQuerying",
                "params": {
                    "context": {
                        "userInput": {
                            "from": {
                                "title": from_name,
                                "key": from_city.code,
                                "slug": context['from']['slug']
                            },
                            "to": {
                                "title": to_name,
                                "key": to_city.code,
                                "slug": context['to']['slug']
                            }
                        },
                        "transportType": "plane",
                        "from": context['from'],
                        "originalFrom": context['originalFrom'],
                        "to": context['to'],
                        "originalTo": context['to'],
                        "searchNext": False,

                    }
                }
            }]
        }