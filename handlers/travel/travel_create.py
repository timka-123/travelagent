import datetime
import sys

import pytz
from sqlalchemy.orm import create_session
from tzwhere import tzwhere
import traceback
import timezonefinder

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import engine, Location, Travel, User
from utils import TravelCreateStates, OpenStreetMapsClient,string2date

router = Router()


@router.callback_query(F.data == "createtravel")
async def request_travel_name(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="home"
        )
    )
    await call.message.edit_text(
        text=f"📝 Введите название вашего нового путешествия (не больше 25 символов)",
        reply_markup=builder.as_markup()
    )
    await state.set_state(TravelCreateStates.ENTER_NAME)


@router.message(TravelCreateStates.ENTER_NAME)
async def request_locations(message: Message, state: FSMContext):
    name = message.text
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="home"
        )
    )
    if not name or len(name) > 25:
        return await message.answer(
            text="😞 Увы, но введенное название больше 25 символов",
            reply_markup=builder.as_markup()
        )
    await state.update_data(name=name)
    await state.set_state(TravelCreateStates.ENTER_DESCRIPTION)
    await message.answer(
        text="📝 Записал, а теперь, пожалуйста, введите описание путешествия. Если вводить нечего, то нажмите на  /skip",
        reply_markup=builder.as_markup()
    )


@router.message(TravelCreateStates.ENTER_DESCRIPTION)
async def request_location(message: Message, state: FSMContext):
    description = message.text
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="home"
        )
    )
    if not description or len(description) > 1024:
        return await message.answer(
            text="☹️ Сожалеем, но вы не можете ввести описание больше 1024 символов",
            reply_markup=builder.as_markup()
        )
    if description == "/skip":
        description = "Описание не указано"
    await state.update_data(description=description)
    await state.set_state(TravelCreateStates.ENTER_SECOND_LOCATION)
    await message.answer(
        text=f"📍 Отправьте, пожалуйста, точку на карте, где Вы хотите остановиться. Это нужно, "
             f"чтобы указать их в качестве второй точки путешествия.",
        reply_markup=builder.as_markup()
    )


@router.message(TravelCreateStates.ENTER_SECOND_LOCATION, F.location)
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
    await state.set_state(TravelCreateStates.ENTER_TIMES)


@router.message(TravelCreateStates.ENTER_TIMES)
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
        travel = Travel(
            name=data['name'],
            description=data['description'],
            user=message.from_user.id
        )
        session.add(travel)
        session.commit()

        location = Location(
            date_start=start_date,
            date_end=end_date,
            timezone=offset,
            travel=travel.id,
            user=message.from_user.id,
            lat=data['coords']['lat'],
            lon=data['coords']['lon'],
            place=data['city']
        )

        session.add(location)
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
        text="✅ Путешествие создано",
        reply_markup=InlineKeyboardBuilder().row(
            InlineKeyboardButton(text="💠 Управление путешествием", callback_data=f"travel|{travel.id}")
        ).as_markup()
    )
