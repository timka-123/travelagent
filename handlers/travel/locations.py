import sys
import traceback
from logging import error

import pytz
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session
from timezonefinder import timezonefinder

from database import engine, Location, Travel, User
from utils import LocationEditStates, string2date, OpenStreetMapsClient, LocationCreateStates

router = Router()


@router.callback_query(F.data.startswith("tlocations"))
async def locations(call: CallbackQuery):
    travel_id = call.data.split("|")[1]
    session = create_session(engine)
    locations = session.query(Location).filter_by(travel=int(travel_id)).order_by(Location.date_start)
    session.close()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Создать", callback_data=f"newloc|{travel_id}")
    )
    for location in locations:
        builder.add(
            InlineKeyboardButton(text=f"#{location.id} - {location.place}", callback_data=f"eloc|{location.id}")
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{travel_id}")
    )
    await call.message.edit_text(
        text="💠 Ниже вы видите список локаций. Нажмите на нужную для получения информации о ней",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("newloc|"))
async def request_location(call: CallbackQuery, state: FSMContext):
    await state.update_data(travel_id=call.data.split("|")[1])
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=f"tlocations|{call.data.split('|')[1]}"
        )
    )
    await state.set_state(LocationCreateStates.ENTER_LOCATIONS)
    await call.message.edit_text(
        text=f"📍 Отправьте, пожалуйста, точку на карте, где Вы хотите остановиться",
        reply_markup=builder.as_markup()
    )


@router.message(LocationCreateStates.ENTER_LOCATIONS, F.location)
async def process_sent_venue(message: Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    client = OpenStreetMapsClient()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="home"
        )
    )
    city = await client.get_location_info(lat, lon)
    if not city:
        return await message.answer(
            text="☹️ Увы, но я не смог найти город или деревню по данной точке локации",
            reply_markup=builder.as_markup()
        )
    await state.update_data(city=city.city_name)
    await state.update_data(coords={
        "lat": lat,
        "lon": lon
    })
    await message.answer(
        text="""⌚ Подскажите даты, в которые вы проведете в городе. Будет использоваться локальное время в данной локации

📅 <code>день.месяц.год час:минуты (дата начала) - день.месяц.год час:минуты (дата окончания)</code>

Пример ввода: <code>12.02.2024 12:00 - 14.02.2024 14:00</code>""",
        reply_markup=builder.as_markup()
    )
    await state.set_state(LocationCreateStates.ENTER_TIMES)


@router.message(LocationCreateStates.ENTER_TIMES)
async def process_time(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="home"
        )
    )
    # parse argument
    try:
        start_str_date, end_str_date = message.text.split(" - ")
        start_date = string2date(start_str_date)
        end_date = string2date(end_str_date)

        # parse timezone
        data = await state.get_data()
        tf = timezonefinder.TimezoneFinder()
        timezone_str = tf.certain_timezone_at(lat=data['coords']['lat'], lng=data['coords']['lon'])
        timezone = pytz.timezone(timezone_str)
        offset = timezone.utcoffset(start_date).total_seconds()

        # add location
        session = create_session(engine)
        user = session.get(User, message.from_user.id)

        client = OpenStreetMapsClient()
        current_city = await client.get_city(user.city)

        # add travel
        travel = data['travel_id']

        location = Location(
            date_start=start_date,
            date_end=end_date,
            timezone=offset,
            travel=travel,
            user=message.from_user.id,
            lat=data['coords']['lat'],
            lon=data['coords']['lon'],
            place=data['city']
        )

        session.add(location)
        session.commit()

        session.commit()

        session.close()
    except Exception as e:
        ex_type, ex, tb = sys.exc_info()
        traceback.print_tb(tb)
        print(e)
        return await message.answer(
            text=f"""<b>❌ Неверный формат ввода даты</b>

📅 <code>день.месяц.год час:минуты (дата начала) - день.месяц.год час:минуты (дата окончания)</code>

Пример ввода: <code>12.02.2024 12:00 - 14.02.2024 14:00</code>"""
        )
    await message.answer(
        text="✅ Точка создана",
    )
    location_id = location.id
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💠 Местоположение", callback_data=f"eeloc|place|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓️ Начало", callback_data=f"eeloc|date_start|{location_id}"),
        InlineKeyboardButton(text="🗓️ Конец", callback_data=f"eeloc|date_end|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"eeloc|delete|{location.id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Назад", callback_data=f"tlocations|{location.travel}"),
    )
    await message.answer(
        text=f"""<b>💠 Информация о локации</b>

🆔 ID: #{location.id}
📍 Местоположение: <code>{location.lat} {location.lon}</code>
🗓️ Начало: {location.date_start.strftime("%d.%m.%Y")}
🗓️ Конец: {location.date_end.strftime("%d.%m.%Y")}
        """,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("eloc|"))
async def location_info(call: CallbackQuery, state: FSMContext):
    await state.clear()
    location_id = call.data.split("|")[1]
    session = create_session(engine)
    location = session.get(Location, location_id)
    session.close()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💠 Местоположение", callback_data=f"eeloc|place|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓️ Начало", callback_data=f"eeloc|date_start|{location_id}"),
        InlineKeyboardButton(text="🗓️ Конец", callback_data=f"eeloc|date_end|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"eeloc|delete|{location.id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Назад", callback_data=f"tlocations|{location.travel}"),
    )
    await call.message.edit_text(
        text=f"""<b>💠 Информация о локации</b>

🆔 ID: #{location.id}
📍 Местоположение: <code>{location.lat} {location.lon}</code>
🗓️ Начало: {location.date_start.strftime("%d.%m.%Y")}
🗓️ Конец: {location.date_end.strftime("%d.%m.%Y")}
""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("eeloc"))
async def edit_location_info(call: CallbackQuery, state: FSMContext):
    cmd, action, location_id = call.data.split("|")

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"eloc|{location_id}")
    )
    await state.update_data(
        action=action,
        location_id=location_id
    )
    await state.set_state(LocationEditStates.EDIT_INFO)
    if action == "date_start":
        await call.message.edit_text(
            text="📝 Введите новую дату начала в формате <code>12.02.2024 12:00</code>",
            reply_markup=builder.as_markup()
        )
    elif action == "date_end":
        await call.message.edit_text(
            text="📝 Введите новую дату конца в формате <code>12.02.2024 12:00</code>",
            reply_markup=builder.as_markup()
        )
    elif action == "place":
        await call.message.edit_text(
            text="📍 Отправьте точку на карте, где будет новое местоположение",
            reply_markup=builder.as_markup()
        )
    elif action == "delete":
        await state.clear()
        session = create_session(engine)
        location = session.get(Location, location_id)
        session.delete(location)
        session.commit()
        locations = session.query(Location).filter_by(travel=int(location.travel)).order_by(Location.date_start)
        session.close()
        builder = InlineKeyboardBuilder()
        for location in locations:
            builder.add(
                InlineKeyboardButton(text=f"#{location.id} - {location.place}", callback_data=f"eloc|{location.id}")
            )
        builder.adjust(2)
        builder.row(
            InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{location.travel}")
        )
        await call.message.edit_text(
            text="💠 Ниже вы видите список локаций. Нажмите на нужную для получения информации о ней",
            reply_markup=builder.as_markup()
        )
        await call.answer("✅ Успешно")


@router.message(LocationEditStates.EDIT_INFO)
async def apply_new_location_info(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    location_id = int(data['location_id'])

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"eloc|{location_id}")
    )

    session = create_session(engine)
    location = session.get(Location, location_id)

    if action == "date_start":
        try:
            new_date = string2date(message.text)
            location.date_start = new_date
            session.commit()
        except Exception as e:
            error(e)
            return await message.answer(
                text="❌ Неверный формат ввода даты. Попробуйте еще раз",
                reply_markup=builder.as_markup()
            )
    elif action == "date_end":
        try:
            new_date = string2date(message.text)
            location.date_end = new_date
            session.commit()
        except Exception as e:
            error(e)
            return await message.answer(
                text="❌ Неверный формат ввода даты. Попробуйте еще раз",
                reply_markup=builder.as_markup()
            )
    elif action == "place":
        if not location:
            return await message.answer(
                text="❌ Вы отправили не точку на карте",
                reply_markup=builder.as_markup()
            )
        lat, lon = message.location.latitude, message.location.longitude
        client = OpenStreetMapsClient()
        city = await client.get_location_info(lat, lon)
        if not city:
            return await message.answer(
                text="☹️ Увы, но я не смог найти город или деревню по данной точке локации",
                reply_markup=builder.as_markup()
            )
        location.lat = lat
        location.lon = lon
        location.place = city.city_name
        session.commit()

    session.close()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💠 Местоположение", callback_data=f"eeloc|place|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓️ Начало", callback_data=f"eeloc|date_start|{location_id}"),
        InlineKeyboardButton(text="🗓️ Конец", callback_data=f"eeloc|date_end|{location_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"eeloc|delete|{location.id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Назад", callback_data=f"tlocations|{location.travel}"),
    )
    await message.answer(
        text=f"""<b>💠 Информация о локации</b>

🆔 ID: #{location.id}
📍 Местоположение: <code>{location.lat} {location.lon}</code>
🗓️ Начало: {location.date_start.strftime("%d.%m.%Y")}
🗓️ Конец: {location.date_end.strftime("%d.%m.%Y")}
    """,
        reply_markup=builder.as_markup()
    )
