from pyairports.airports import Airports
from aiohttp import ClientSession
from googletrans import Translator


class Aviasales:
    def __init__(self):
        self.base_url = "https://ariadne.aviasales.com/api/gql"
        self.session = ClientSession(headers={
            "User-Agent": ""
        })
        self.airports = Airports()
        self.translator = Translator()

    async def get_tickets(self, city_from: str, city_to: str) -> list[dict]:
        iata_from = ""
        iata_to = ""

        city_from = self.translator.translate(city_from, dest="en").text
        if city_from == "Moscow":
            iata_from = "MOW"
        city_to = self.translator.translate(city_to, dest="en").text
        if city_to == "Moscow":
            iata_to = "MOW"
        for key, item in self.airports.other.items():
            if item.name == city_from:
                iata_from = key
            elif item.name == city_to:
                iata_to = key
        
        data = {
            "query": "query DirectionPageBlocksQuery($brand: Brand!, $input: DirectionPageBlocksV2Input!, $locales: [String!], $expandServices: Boolean!) {\n    direction_page_blocks_v2(input: $input, brand: $brand) {\n      blocks {\n        __typename\n        \n  ... on HowToGet @skip (if: $expandServices) {\n    blocks {\n      __typename\n      \n      ... on HowToGetContentlessBlock {\n        type\n      }\n\n      ... on HowToGetCustomBlock {\n        id\n        title\n        icon_url\n        target {\n          kind\n          url\n        }\n      }\n\n      ... on HowToGetDirectFlights {\n        to_destination {\n          ...howToGetDirectFlightsFields\n        }\n\n        from_destination {\n          ...howToGetDirectFlightsFields\n        }\n      }\n\n      ... on HowToGetTravelRestrictions {\n        open\n      }\n\n      ... on HowToGetTravelRestrictionsV2 {\n        title\n        subtitle\n        button {\n          title\n          icon {\n            token {\n              icon\n              size\n            }\n          }\n          color_theme\n        }\n      }\n    }\n  }\n\n\n  ... on Bullet {\n    emoji {\n      svg\n    }\n    text\n    bulletTitle: title\n    buttons {\n      title\n      url\n      type\n      payload {\n        ... on TravelRestrictionsButtonPayload {\n          title\n          subtitle\n        }\n\n        ... on UrlButtonPayload {\n          url\n        }\n      }\n    }\n  }\n\n\n  ... on CheapTickets {\n    tickets {\n      __typename\n      ... on Price {\n        ...priceFields\n      }\n      ... on HotOffer {\n        price {\n          ...priceFields\n        }\n        old_price {\n          value\n        }\n      }\n    }\n    places {\n      cities {\n        ...citiesFields\n      }\n      airports {\n        ...airportsFields\n      }\n      airlines {\n        ...airlinesFields\n      }\n    }\n  }\n  \n\n  ... on PriceChart @include (if: $expandServices) {\n    __typename\n    prices {\n      price {\n        ...priceFields\n      }\n      stats {\n        depart_low\n        depart_value\n        return_low\n        return_value\n      }\n    }\n  }\n  \n\n  ... on Providers {\n    providers {\n      id\n      first_name\n      last_name\n      role\n      avatar_url\n      is_ambassador\n      tags\n      contacts {\n        url\n        type\n        title\n        contact_title\n        icon {\n          svg\n        }\n      }\n    }\n  }\n\n\n  ... on Header {\n    title\n    headerSubtitle: subtitle\n  }\n\n\n  ... on Bullets {\n    title\n    bullets {\n      emoji {\n        svg\n      }\n      text\n      buttons {\n        title\n        url\n      }\n    }\n  }\n\n\n  ... on CarouselV2 {\n    group_id\n    location_id\n    title\n    subtitle\n    type\n    button {\n      navigation {\n        deeplink\n        group_id\n        type\n      }\n      text\n    }\n    carouselPlaces: places {\n      background_color\n      id\n      image_url\n      name\n      description\n      navigation {\n        deeplink\n        group_id\n        type\n      }\n      badge {\n        style {\n          background_color {\n            dark\n            light\n          }\n          text_color {\n            dark\n            light\n          }\n        }\n        text\n      }\n      config {\n        aspect_ratio\n      }\n    }\n  }\n\n\n\n  ... on DirectFlights @include (if: $expandServices) {\n    from_destination {\n        ...scheduleDayFields\n    }\n    to_destination {\n        ...scheduleDayFields\n    }\n  }\n\n\n    ... on NatureFeedEntrypoint {\n        header\n        preview_image_url\n        video_title\n        video_url\n        button_text\n        nature_feed_id  \n        location_id\n    }\n    \n    ... on NatureFeedEntrypointCompilation {\n        entrypoints {\n            preview_image_url\n            video_title\n            video_url\n            button_text\n            nature_feed_id  \n            location_id\n            badge {\n                style {\n                    background_color {\n                        dark\n                        light\n                    }\n                    text_color {\n                        dark\n                        light\n                    }\n                }\n                text\n            }\n        }\n        header\n        analytics {\n            destination\n            guide_ark_id\n            origin\n            screen_content_type\n        }\n    }\n\n\n  ... on PSGR {\n    __typename\n    articles {\n      title\n      subtitle\n      image_url\n      url\n    }\n  }\n  \n\n  ... on HowToGetTravelRestrictionsV2 {\n    __typename\n    title\n    subtitle\n    restrictionButton: button {\n      title\n    }\n  }\n\n      }\n    }\n  }\n  \nfragment howToGetDirectFlightsFields on ScheduleDay {\n  flights {\n    origin_airport_iata\n    destination_airport_iata\n    departure_date_time\n    airline\n  }\n  depart_date\n}\n\n\nfragment priceFields on Price {\n  depart_date\n  return_date\n  value\n  cashback\n  found_at\n  signature\n  ticket_link\n  currency\n  provider\n  with_baggage\n  segments {\n    transfers {\n      duration_seconds\n      country_code\n      visa_required\n      night_transfer\n      at\n      to\n      tags\n    }\n    flight_legs {\n      origin\n      destination\n      local_depart_date\n      local_depart_time\n      local_arrival_date\n      local_arrival_time\n      flight_number\n      operating_carrier\n      aircraft_code\n      technical_stops\n      equipment_type\n      duration_seconds\n    }\n  }\n}\n\n\nfragment citiesFields on CityInfo {\n  city {\n    iata\n    translations(filters: {locales: $locales})\n  }\n}\n\nfragment airportsFields on Airport {\n  iata\n  translations(filters: {locales: $locales})\n  city {\n    iata\n    translations(filters: {locales: $locales})\n  }\n}\n\nfragment airlinesFields on Airline {\n  iata\n  translations(filters: {locales: $locales})\n}\n\nfragment scheduleDayFields on ScheduleDay {\n  flights {\n    origin_airport_iata\n    destination_airport_iata\n    departure_date_time\n    airline\n  }\n  depart_date\n  min_price {\n    value\n    currency\n  }\n}\n\n  ",
            "variables": {
                "brand": "AS",
                "expandServices": True,
                "input": {
                    "one_way": True,
                    "source_place": None,
                    "blocks_order": "ALTERED",
                    "market": "ru",
                    "language": "ru",
                    "origin": {
                        "iata": iata_from,
                        "place_type": "CITY"
                    },
                    "destination": {
                        "flightable_place": {
                            "iata": iata_to,
                            "place_type": "CITY"
                        }
                    },
                    "currency": "rub",
                    "passport_country": "RU",
                    "auid": "c2VxNmd2lB1NaERsV1hlAg==",
                    "application": "selene",
                    "trip_class": "Y"
                }
            },
            "operation_name": "direction_page_blocks_v2"
        }
        response = await self.session.post(
            url=self.base_url,
            json=data
        )
        resp_data = await response.json()
        return resp_data['data']['direction_page_blocks_v2']['blocks'][1]['tickets']
