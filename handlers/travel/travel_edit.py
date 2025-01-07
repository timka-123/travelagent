import random
import string
from typing import List, Literal

import staticmaps
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, Travel, Location
from database.models.users import User
from utils import TravelEditStates, YandexSchedule, Aviasales, SelectedVariant
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
        InlineKeyboardButton(text="✈️ Найти самолеты", callback_data=f"aviamarshrut|{travel_id}"),
        InlineKeyboardButton(text="🚂 Найти поезда", callback_data=f"trainmarshrut|{travel_id}"),
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
        InlineKeyboardButton(text="✈️ Найти самолеты", callback_data=f"aviamarshrut|{travel_id}"),
        InlineKeyboardButton(text="🚂 Найти поезда", callback_data=f"trainmarshrut|{travel_id}"),
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


@router.callback_query(F.data.startswith("aviamarshrut|"))
async def make_avia_marshrut(call: CallbackQuery, state: FSMContext):
    msg = await call.message.answer("<i>⏳ Ищу подходящие выгодные варианты, пожалуйста, подождите...</i>")
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    user = session.get(User, call.from_user.id)
    session.close()
    
    schedule = YandexSchedule(config.yandex_schedule_api_key)
    variants = await schedule.get_avia(user.city, locations[0].place, locations[0].date_start)
    builder = InlineKeyboardBuilder()
    variants_dict = {}
    for variant in variants[:5]:
        variants_dict[variant['title']] = variant['link']
        builder.row(
            InlineKeyboardButton(text=variant['title'], callback_data=f"smv|avia|{travel_id}|{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}")
        )
    await msg.edit_text(
        text="✈️ Нашел выгодные варианты, попробуйте!",
        reply_markup=builder.as_markup()
    )
    await state.update_data(all_variants=variants_dict, next_ind=1, curr_ind=0, selected_variants={})
    await state.set_state(SelectedVariant.ENTER_VARIANT)


@router.callback_query(F.data.startswith("trainmarshrut|"))
async def make_train_marshrut(call: CallbackQuery, state: FSMContext):
    msg = await call.message.answer("<i>⏳ Ищу подходящие выгодные варианты, пожалуйста, подождите...</i>")
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    user = session.get(User, call.from_user.id)
    session.close()
    
    schedule = YandexSchedule(config.yandex_schedule_api_key)
    variants = await schedule.get_trains(user.city, locations[0].place, locations[0].date_start)
    builder = InlineKeyboardBuilder()
    variants_dict = {}
    for variant in variants[:5]:
        variants_dict[variant['title']] = variant['link']
        builder.row(
            InlineKeyboardButton(text=variant['title'], callback_data=f"smv|train|{travel_id}|{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}")
        )
    await msg.edit_text(
        text="🚂 Нашел выгодные варианты, попробуйте!",
        reply_markup=builder.as_markup()
    )
    await state.update_data(all_variants=variants_dict, next_ind=1, curr_ind=0, selected_variants={})
    await state.set_state(SelectedVariant.ENTER_VARIANT)


@router.callback_query(F.data.startswith("smv"), SelectedVariant.ENTER_VARIANT)
async def selected_variant(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    travel_id = int(call.data.split("|")[-2])
    selected_variants: dict[str, str] = data['selected_variants']
    marshrut_type: Literal['avia', 'train'] = call.data.split("|")[1]
    all_variants: dict[str, str] = data['all_variants']
    next_ind: int = data['next_ind']
    curr_ind: int = data['curr_ind']

    for button in call.message.reply_markup.inline_keyboard:
        button = button[0]
        if button.callback_data == call.data:
            selected_variants[button.text] = all_variants[button.text]

    session = create_session(engine)

    locations = session.query(Location).filter_by(travel=travel_id).order_by(Location.date_start).all()
    user = session.get(User, call.from_user.id)
    session.close()

    builder = InlineKeyboardBuilder()
    send_new_message = False
    changed_marshrut_type = False

    if len(selected_variants) == len(locations) + 1:
        for title, link in selected_variants.items():
            builder.row(
                InlineKeyboardButton(text=title, url=link)
            )
        await call.message.edit_text(
            text='✅ Все, закончили! Ниже находятся ссылки на покупку выбранных билетов\n\nДанная функция работает по API сервисов <a href="https://rasp.yandex.ru">Яндекс.Расписание</a> и <a href="https://travel.yandex.ru">Яндекс.Путешествия</a>',
            reply_markup=builder.as_markup(),
            disable_web_page_preview=True
        )
        return
    elif len(selected_variants) == len(locations):
        await call.message.edit_text(
            text="✅ Закончили с подбором билетов по путешествию. Дальше будет выбор обратных билетов (до вашего города)",
            reply_markup=None
        )
        send_new_message = True
        second_place = user.city
        first_place = locations[-1].place
    else:
        first_place = locations[curr_ind].place
        second_place = locations[next_ind].place
    
    schedule = YandexSchedule(config.yandex_schedule_api_key)
    if marshrut_type == "train":
        variants = await schedule.get_trains(first_place, second_place, locations[curr_ind].date_end)
    else:
        variants = await schedule.get_avia(first_place, second_place, locations[curr_ind].date_end)
    if not variants:
        changed_marshrut_type = True
        if marshrut_type == "train":
            variants = await schedule.get_avia(first_place, second_place, locations[curr_ind].date_end)
        else:
            variants = await schedule.get_trains(first_place, second_place, locations[curr_ind].date_end)
    if not variants:
        await call.message.edit_text(
            text=f"😔 Не удалось найти маршрут по направлению <b>{first_place} -> {second_place}</b> через агрегаторы авиа и ж/д билетов."
        )
        return
    for variant in variants[:5]:
        all_variants[variant['title']] = variant['link']
        builder.row(
            InlineKeyboardButton(text=variant['title'], callback_data=f"smv|{marshrut_type}|{travel_id}|{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}")
        )
    if send_new_message:
        await call.message.answer(
            text=f"⏳ Продолжаем...\n\n{'Мы были вынуждены изменить тип транспорта, так как мы не нашли билетов на выбранный тип.' if changed_marshrut_type else ''}",
            reply_markup=builder.as_markup()
        )
    else:
        await call.message.edit_text(
            text=f"⏳ Продолжаем...\n\n{'Мы были вынуждены изменить тип транспорта, так как мы не нашли билетов на выбранный тип.' if changed_marshrut_type else ''}",
            reply_markup=builder.as_markup()
        )
    await call.answer("✅ Понял. Можете выбирать дальше.")
    await state.update_data(selected_variants=selected_variants, next_ind=next_ind + 1, 
                            curr_ind=next_ind, all_variants=all_variants)
