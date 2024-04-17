from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, User
from utils import ProfileEditStates, OpenStreetMapsClient


router = Router()


@router.callback_query(F.data == "profile")
async def profile_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📝 Имя", callback_data=f"prchange|name"),
        InlineKeyboardButton(text="⏰ Возраст", callback_data=f"prchange|age"),
        InlineKeyboardButton(text="📍 Местоположение", callback_data=f"prchange|place"),
        InlineKeyboardButton(text="📝 О себе", callback_data=f"prchange|bio"),
    )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data="home")
    )

    session = create_session(engine)
    user = session.get(User, call.from_user.id)
    session.close()

    await call.message.edit_text(
        text=f"""<b>🤖 Информация о вас</b>
        
📝 Имя: <b>{user.name}</b>
⏰ Возраст: <i>{user.age} лет</i>
📍 Местоположение: <b>{user.country} - {user.city}</b>
📝 О себе: <code>{user.bio}</code>

📝 Для изменения параметров выберите нужный пункт на кливиатуре ниже
""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("prchange|"))
async def request_need_data(call: CallbackQuery, state: FSMContext):
    action = call.data.split("|")[1]
    await state.set_state(ProfileEditStates.ENTER_DATA)
    await state.update_data(action=action)
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="profile")
    )

    if action == "name":
        await call.message.edit_text(
            text="📝 Введите новое имя",
            reply_markup=builder.as_markup()
        )
    elif action == "bio":
        await call.message.edit_text(
            text="📝 Введите новое описание Вашего профиля",
            reply_markup=builder.as_markup()
        )
    elif action == "age":
        await call.message.edit_text(
            text="📝 Введите Ваш возраст",
            reply_markup=builder.as_markup()
        )
    elif action == "place":
        await call.message.edit_text(
            text="📍 Отправьте Вашу текущую локацию, или введите город и страну через пробел",
            reply_markup=builder.as_markup()
        )


@router.message(ProfileEditStates.ENTER_DATA)
async def apply_data(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    session = create_session(engine)
    user = session.get(User, message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="profile")
    )

    if action == "place":
        client = OpenStreetMapsClient()
        if message.location:
            city = await client.get_location_info(
                lat=message.location.latitude,
                lon=message.location.longitude
            )
            if not city:
                return await message.answer(
                    text=f"❌ Не смог найти населенный пункт по отправленной геолокации",
                    reply_markup=builder.as_markup()
                )
            user.city = city.city_name
            user.country = city.country
            session.commit()
        else:
            parts = message.text.split()
            country = parts[-1]
            try:
                parts.remove(country)
                user.country = country
                info = await client.get_city(user.city)
                if not info:
                    return await message.answer(
                        text=f"❌ Не смог найти населенный пункт",
                        reply_markup=builder.as_markup()
                    )
                user.city = " ".join(parts)
                user.country = country
                session.commit()
            except:
                return await message.answer(
                    text=f"❌ Не смог обработать отправленные данные",
                    reply_markup=builder.as_markup()
                )
    elif action == "bio":
        user.bio = message.text
        try:
            session.commit()
        except:
            return await message.answer(
                text=f"❌ Не смог обработать отправленные данные",
                reply_markup=builder.as_markup()
            )
    elif action == "name":
        user.name = message.text
        try:
            session.commit()
        except:
            return await message.answer(
                text=f"❌ Не смог обработать отправленные данные",
                reply_markup=builder.as_markup()
            )
    elif action == "age":
        user.age = int(message.text)
        try:
            session.commit()
        except:
            return await message.answer(
                text=f"❌ Не смог обработать отправленные данные",
                reply_markup=builder.as_markup()
            )
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📝 Имя", callback_data=f"prchange|name"),
        InlineKeyboardButton(text="⏰ Возраст", callback_data=f"prchange|age"),
        InlineKeyboardButton(text="📍 Местоположение", callback_data=f"prchange|place"),
        InlineKeyboardButton(text="📝 О себе", callback_data=f"prchange|bio"),
    )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data="home")
    )

    session = create_session(engine)
    user = session.get(User, message.from_user.id)
    session.close()

    await message.answer(
        text=f"""<b>🤖 Информация о вас</b>

📝 Имя: <b>{user.name}</b>
⏰ Возраст: <i>{user.age} лет</i>
📍 Местоположение: <b>{user.country} - {user.city}</b>
📝 О себе: <code>{user.bio}</code>

📝 Для изменения параметров выберите нужный пункт на кливиатуре ниже
    """,
        reply_markup=builder.as_markup()
    )
