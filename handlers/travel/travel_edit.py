from typing import List

import staticmaps
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, Travel, Location
from utils import TravelEditStates, YandexSchedule, Aviasales
from config import config

router = Router()


@router.callback_query(F.data.startswith("travel|"))
async def travel_info(call: CallbackQuery, state: FSMContext):
    await state.clear()
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)
    travel = session.get(Travel, travel_id)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    session.close()

    loc_string = ""
    for location in locations:
        index = locations.index(location) + 1
        loc_string += (f"#{index} - {location.place}.\nНачало: <code>{location.date_start.strftime('%m/%d/%Y')}</code"
                       f">. Окончание: <code>{location.date_end.strftime('%m/%d/%Y')}</code>\n\n")

    if not travel:
        return await call.answer(
            text="❌ Ошибка при получении путешествия"
        )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✈️ Найти поезда", callback_data=f"trainmarshrut|{travel_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="📝 Изменть название", callback_data=f"tedit|name|{travel_id}"),
        InlineKeyboardButton(text="📝 Изменть описание", callback_data=f"tedit|description|{travel_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="💠 Изменить локации", callback_data=f"tlocations|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🤖 Со-путешественники", callback_data=f"tinvite|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Заметки", callback_data=f"tnotes|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travels")
    )
    await call.message.edit_text(
        text=f"""<b>📍 Путешествие #{travel_id}</b>

<b>💠 Локации</b>        
{loc_string}

📝 Название: <b>{travel.name}</b>
📝 Описание: <code>{travel.description}</code>
""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("tedit"))
async def edit_travel_details(call: CallbackQuery, state: FSMContext):
    action, travel_id = call.data.split("|")[1], call.data.split("|")[2]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"travel|{travel_id}")
    )

    await state.update_data(travel_id=travel_id)
    if action == "name":
        await call.message.edit_text(
            text="📝 Введите новое название путешествия",
            reply_markup=builder.as_markup()
        )
        await state.set_state(TravelEditStates.ENTER_NAME)
    elif action == "description":
        await call.message.edit_text(
            text="📝 Введите новое описание путешествия",
            reply_markup=builder.as_markup()
        )
        await state.set_state(TravelEditStates.ENTER_DESCRIPTION)


async def send_menu(message: Message, travel_id: int, travel: Travel, locations: List[Location]):
    builder = InlineKeyboardBuilder()
    loc_string = ""
    for location in locations:
        index = locations.index(location) + 1
        loc_string += (f"#{index} - {location.place}.\nНачало: <code>{location.date_start.strftime('%m/%d/%Y')}</code"
                       f">. Окончание: <code>{location.date_end.strftime('%m/%d/%Y')}</code>\n\n")
    builder.row(
        InlineKeyboardButton(text="✈️ Найти поезда", callback_data=f"trainmarshrut|{travel_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="📝 Изменить название", callback_data=f"tedit|name|{travel_id}"),
        InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"tedit|description|{travel_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="💠 Изменить локации", callback_data=f"tlocations|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🤖 Со-путешественники", callback_data=f"tinvite|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Заметки", callback_data=f"tnotes|{travel_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travels")
    )
    await message.answer(
        text=f"""<b>📍 Путешествие #{travel_id}</b>

<b>💠 Локации</b>        
{loc_string}

📝 Название: <b>{travel.name}</b>
📝 Описание: <code>{travel.description}</code>
    """,
        reply_markup=builder.as_markup()
    )


@router.message(TravelEditStates.ENTER_NAME)
async def apply_new_name(message: Message, state: FSMContext):
    data = await state.get_data()
    session = create_session(engine)
    travel = session.get(Travel, data['travel_id'])
    locations = session.query(Location).filter_by(travel=data['travel_id']).order_by(Location.date_start).all()
    travel.name = message.text
    session.commit()
    session.close()
    await state.clear()
    await send_menu(message, data['travel_id'], travel, locations)


@router.message(TravelEditStates.ENTER_DESCRIPTION)
async def apply_new_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    session = create_session(engine)
    travel = session.get(Travel, data['travel_id'])
    locations = session.query(Location).filter_by(travel=data['travel_id']).order_by(Location.date_start).all()
    travel.description = message.text
    session.commit()
    session.close()
    await state.clear()
    await send_menu(message, data['travel_id'], travel, locations)


@router.callback_query(F.data.startswith("marshrut|"))
async def marshrut_callback(call: CallbackQuery):
    msg = await call.message.answer("⏳ Рисую маршрут, это может занять некоторое время")
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    session.close()

    dots = []
    context = staticmaps.Context()
    context.set_tile_provider(staticmaps.tile_provider_OSM)
    for location in locations:
        dot = staticmaps.create_latlng(location.lat, location.lon)
        dots.append(dot)
        context.add_object(staticmaps.Marker(dot, color=staticmaps.RED, size=12))

    for i in range(len(dots) // 2):
        try:
            dot1 = dots[i]
            dot2 = dots[i + 1]
            context.add_object(staticmaps.Line([dot1, dot2], color=staticmaps.BLUE, width=4))
        except IndexError:
            ...

    image = context.render_cairo(800, 500)
    image.write_to_png("marshrut.png")
    photo = FSInputFile("marshrut.png")
    await msg.delete()
    await call.message.answer_photo(
        photo=photo,
        caption="💠 Ваш маршрут готов!"
    )


@router.callback_query(F.data.startswith("trainmarshrut|"))
async def make_train_marshrut(call: CallbackQuery):
    msg = await call.message.answer("<i>⏳ Ищу подходящие выгодные варианты, пожалуйста, подождите...</i>")
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    session.close()

    if len(locations) != 2:
        return await msg.edit_text("❌ Увы, я пока что не могу строить маршруты больше, чем на 2 точки")
    
    schedule = YandexSchedule(config.yandex_schedule_api_key)
    variants = await schedule.get_trains(locations[0].place, locations[1].place, locations[0].date_end)
    builder = InlineKeyboardBuilder()
    for variant in variants[:5]:
        builder.row(
            InlineKeyboardButton(text=variant['title'], url=variant['link'])
        )
    await msg.edit_text(
        text="🚂 Нашел выгодные варианты, попробуйте!",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("aviamarshrut|"))
async def avia_marshrut(call: CallbackQuery):
    msg = await call.message.answer("<i>⏳ Ищу подходящие авиабилеты, это займет некоторое время</i>")
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    session.close()

    if len(locations) != 2:
        return await msg.edit_text("❌ Увы, я пока что не могу строить маршруты больше, чем на 2 точки")
    
    aviasales = Aviasales()

    builder = InlineKeyboardBuilder()

    tickets = await aviasales.get_tickets(locations[0].place, locations[1].place)
    for ticket in tickets:
        flight = ticket['segments'][0]['flight_legs'][0]
        builder.row(
            InlineKeyboardButton(text=f"{flight['origin']} -> {flight['destination']} ({flight['local_depart_date']} {flight['local_depart_time']})", 
                                 url=f"https://aviasales.ru/search{ticket['ticket_link']}")
        )
    
    await msg.edit_text(
        text="✈️ Собрал подборку авиабилетов. Авиасейлс - самые дешевые авиабилеты!",
        reply_markup=builder.as_markup()
    )