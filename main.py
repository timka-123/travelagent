from logging import basicConfig, INFO
from asyncio import get_event_loop

from config import config
from handlers import (
    start,
    registration,
    travel,
    profile
)


async def main():
    config.dp.include_routers(
        start,
        registration,
        travel.travel_create,
        travel.travel_list,
        travel.travel_edit,
        travel.locations,
        travel.edit_friend,
        travel.add_friend,
        travel.friends,
        travel.notes,
        travel.add_note,
        travel.edit_note,
        profile
    )
    await config.dp.start_polling(config.bot)


if __name__ == '__main__':
    basicConfig(level=INFO)
    loop = get_event_loop()
    loop.run_until_complete(main())
