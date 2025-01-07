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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Cookie": "my=YwA=; yuidss=8494807881714631959; yandexuid=8494807881714631959; yashr=8167406751714631959; receive-cookie-deprecation=1; ymex=2030115158.yrts.1714755158; font_loaded=YSv1; device_id=a9c80dde4965960a76d49d32879929a55afc60e13; amcuid=722060661723285133; skid=7688164521723537502; seoQuery=j%3A%7B%22utmSource%22%3A%22informer%22%2C%22utmMedium%22%3A%22search%22%2C%22utmCampaign%22%3A%22blank%22%2C%22device%22%3A%22desktop%22%7D; yabs-dsp=mts_banner.U1JfX2g4UDVSTDZYWXhFWFR5cnNtQQ==; gdpr=0; _ym_d=1730038916; i=TYWAI5V0dSJ9fvI2fcmHWEitrYf/goDcVCy4r68zEoXcLyvrdCjiybwRKFEOL5TXfxUMSApbTJnfTTyXSSxU896aBWU=; Cookie_check=CheckCookieCheckCookie; yabs-vdrf=A0; yandex_expboxes=1068828%2C0%2C62%3B1131450%2C0%2C31%3B663874%2C0%2C27%3B663859%2C0%2C16%3B1178539%2C0%2C85; experiment__everlastingStationTouchExperiment=1; experiment__everlastingThreadTouchExperiment=; experiment__experiment=; experiment__notCanonicalThreadUid=; experiment__showFlagsInConsole=; experiment__webvisor=; experiment__yabusOfflineLabel=1; fonts-loaded=true; theme=dark; spravka=dD0xNzM1ODk4OTUyO2k9OTQuMTQxLjEwMy4xNzY7RD0wREVCQUU5MEQzNjk5OUNFNzgwOTQ0OEVGODAzNUZBMjk4M0M2NTgxMjFFNkI5MDE5QjgyM0E4NjRCRURFQUQxMkExOEI4NzE5NzNDMjU4MDg5NEQ2NUY3RTRENjFGMEIwRDVFNjk5NDQ3MUM2OTExNjgwQjQ2NTMyOTVDQUU3MTg0QzAzOTJCMzFDNTg1QjRCOTEwMEQ4RThCQkUyNjRCMTI2RjBGREQwNUEyMDUzQkMyNDc4RUZGO3U9MTczNTg5ODk1MjU3Mzk5NjAyMjtoPTc4NGQ0ZTE3OGZkMzhhMDRlMzY3YTYzMTdhOWUxY2Y2; maps_session_id=1735900413196521-9149022521596591532-balancer-l7leveler-kubr-yp-klg-25-BAL; active-browser-timestamp=1735902967200; instruction=1; is_gdpr=0; is_gdpr_b=CNfYHxCYqAIoAg==; Session_id=3:1736084028.5.0.1714668759442:i3GJLQ:1.1.2:1|923476598.-1.2.3:1714668759|1200356602.177509.2.2:177509.3:1714846268|2035154387.21071701.2.2:21071701.3:1735740460|3:10300829.200005.HTdehmNEFSknIzugSaaFShnagVc; sessar=1.1197.CiCtTyrhI8SZJPC2-9LBLD-JAahr8H-rg_I_kpTjoRDIyA.bwVGyUrBEwo47ln_m9d1n31-lCWRaxogU_bexSRMPjQ; sessionid2=3:1736084028.5.0.1714668759442:i3GJLQ:1.1.2:1|923476598.-1.2.3:1714668759|1200356602.177509.2.2:177509.3:1714846268|2035154387.21071701.2.2:21071701.3:1735740460|3:10300829.200005.fakesign0000000000000000000; yp=2051093695.pcs.1#2040566023.2fa.1#2051444028.udn.cDpUaW11cg%3D%3D#2040566023.multib.1#1736338433.szm.1:1920x1080:1689x976#1740917694.atds.1#1767269695.swntab.0#1736597695.dlp.3#1738412095.hdrc.0; L=BF58em9bQWJCAUxYTlJwXnoGfVNjR2hfGhkDSRk=.1736084028.16007.321823.7aabfb8251b576a3b9e94b1d5dc2cb1f; yandex_login=vakzn; ys=udn.cDpUaW11cg%3D%3D#c_chck.495415971; _ym_uid=17360867661028701869; bh=EigiQ2hyb21pdW0iO3Y9IjEzMSIsICJOb3RfQSBCcmFuZCI7dj0iMjQiKgI/MDoHIm1hY09TImDaiuu7Bmoh3MrRtgG78Z+rBPrWhswI0tHt6wP8ua//B9/9k+EE84EC; _yasc=04JqaMcqQUeWYxmqFwEQr4BIjsNd6qRjoycr8CH9hE5TqunvHJi2l2dhxvCJdWbBS1u+eK3+M6eEZJ4qiJOqgLsnuplXIw=="
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
                        "startTime": (dep_datetime - timedelta(days=1)).isoformat() + "Z",
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