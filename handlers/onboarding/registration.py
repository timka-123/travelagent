from aiogram.types import Message, KeyboardButton, InlineKeyboardButton, ReplyKeyboardRemove
from sqlalchemy.orm import create_session
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from database import engine, User, TravelMember, Travel
from utils import RegisterStates, OpenStreetMapsClient


router = Router()


async def request_name(message: Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=message.from_user.first_name)
    )
    await message.answer(
        text=f"""<b>👋 Привет!</b>
        
🤖 Я - бот для более простого составления путешествий. Чтобы продолжить, тебе нужно ввести некоторые данные. Начнем, пожалуй, с твоего имени!

<b>📝 Пожалуйста, отправь мне свое имя! Если оно такое же, как у тебя в телеграме, то просто нажми на кнопку ниже!</b>""",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(RegisterStates.ENTER_NAME)


@router.message(RegisterStates.ENTER_NAME)
async def request_age(message: Message, state: FSMContext):
    await message.answer(
        text=f"📝 Приятно познакомиться, {message.text}! Теперь введи свой возраст <b>числом</b>",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.update_data(name=message.text)
    await state.set_state(RegisterStates.ENTER_AGE)


@router.message(RegisterStates.ENTER_AGE)
async def request_location(message: Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        return await message.answer(
            text=f"""<b>🤔 Хм, кажется, ты ввел не число</b>
            
📝 Пожалуйста, отправь мне просто число, которым обозначается твой возраст"""
        )
    await state.update_data(age=age)
    location_builder = ReplyKeyboardBuilder()
    location_builder.add(
        KeyboardButton(text="📍 Прислать геолокацию", request_location=True)
    )
    await message.answer(
        text="✍️",
        reply_markup=location_builder.as_markup(resize_keyboard=True)
    )
    await message.answer(
        text=f"""<b>✅ Записал, твой возраст: {age}</b>
        
⚠️ Нажми на кнопку ниже, если вдруг ты ошибся при вводе возраста. 

<b>📍 Теперь введи, пожалуйста, город, где ты находишься. Либо, просто отправь свое местоположение по кнопке, которая у тебя открылась вместо клавиатуры.</b>""",
    )
    await state.set_state(RegisterStates.ENTER_CITY)


@router.message(RegisterStates.ENTER_CITY, F.location)
async def apply_location(message: Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    client = OpenStreetMapsClient()
    city = await client.get_location_info(lat, lon)
    if not city:
        return await message.answer(
            text="😔 Не смог определить Ваше местоположение по геолокации. Пожалуйста, отправьте мне <b>название вашего "
                 "города</b>",
            reply_markup=ReplyKeyboardRemove()
        )
    await state.update_data(
        city=city.city_name,
        country=city.country
    )
    await message.answer(
        text=f"""<b>✅ Записал, твой город: {city.city_name}, а страна: {city.country}</b>

✍️ Теперь напиши, пожалуйста, немного информации о себе (до 70 символов). Если не хочешь - просто пропиши /skip""",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegisterStates.ENTER_BIO)


@router.message(RegisterStates.ENTER_CITY)
async def request_country(message: Message, state: FSMContext):
    city = message.text
    client = OpenStreetMapsClient()
    city_data = await client.get_city(city)
    if not city_data:
        return await message.answer(
            text="😔 Не смог найти Ваш город. Возможно, вы опечатались. Пожалуйста, отправьте мне <b>название вашего "
                 "города</b>",
            reply_markup=ReplyKeyboardRemove()
        )
    city = await client.get_location_info(lat=city_data.lat, lon=city_data.lon)
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=city.country)
    )
    await state.update_data(city=city_data.city_name)
    await message.answer(
        text=f"""<b>📝 Записал твой город: {city_data.city_name}</b>
        
Пожалуйста, введи свою страну (если вдруг ты считаешь, что мы определили её неверно)""",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(RegisterStates.ENTER_COUNTRY)


@router.message(RegisterStates.ENTER_COUNTRY)
async def request_bio(message: Message, state: FSMContext):
    country = message.text
    client = OpenStreetMapsClient()
    is_valid = await client.check_if_country_exists(country)
    if not is_valid:
        return await message.answer(
            text="😔 Не смог найти Вашу страну. Возможно, вы опечатались. Пожалуйста, отправьте мне <b>название страны, "
                 "где находится ваш город</b>",
            reply_markup=ReplyKeyboardRemove()
        )
    await state.update_data(country=country)
    await message.answer(
        text=f"""<b>👍 Записал страну: {country}</b>
        
Отправь мне немного информации о себе (до 70 символов). Если не хочешь - нажми на /skip""",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegisterStates.ENTER_BIO)


@router.message(RegisterStates.ENTER_BIO)
async def create_user(message: Message, state: FSMContext, bot):
    bio = message.text
    if len(bio) > 70:
        return await message.answer(
            text="☹️ Длина био не может превышать 70 символов",
            reply_markup=ReplyKeyboardRemove()
        )
    if bio == "/skip":
        bio = "Пользователь ничего о себе не рассказал"
    await state.update_data(bio=bio)
    data = await state.get_data()

    session = create_session(engine)
    user = User(
        id=message.from_user.id,
        age=data['age'],
        city=data['city'],
        country=data['country'],
        bio=data['bio'],
        name=data['name']
    )
    session.add(user)
    session.commit()

    if data.get("travel_id"):
        travel_id = data.get("travel_id")
        travel = session.get(Travel, travel_id)
        travel_member = session.query(TravelMember).filter_by(user_id=message.from_user.id).filter_by(travel_id=travel_id).first()
        if travel_member:
            return await message.answer(
                text="Что-то пошло не так...",
            )

        travel_member = TravelMember(
            user_id=message.from_user.id,
            travel_id=travel_id
        )
        session.add(travel_member)
        session.commit()

        await message.answer(
            text="✅ Вы добавлены в путешествие!",
        )

        # notify all members
        members = session.query(TravelMember).filter_by(travel_id=travel_id).all()
        for member in members:
            try:
                await bot.send_message(
                    chat_id=member.user_id,
                    text=f"""<b>🔔 В путешествие добавлен участник</b>
                    
🆔 Его ID: <code>{travel_member.user_id}</code>

⚠️ Вы получили данное уведомление, поскольку Вы являетесь участником путешествия под названием <b>{travel.name}</b>"""
                )
            except:
                ...

    session.close()
    await message.answer(
        text="✅ Вы зарегистрированы! Пропишите /start для открытия меню"
    )
