from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, TravelMember, User

router = Router()


@router.callback_query(F.data.startswith("tfm|"))
async def show_friend_info(call: CallbackQuery):
    friend_id = int(call.data.split("|")[1])
    session = create_session(engine)
    friend = session.get(TravelMember, friend_id)
    user = session.get(User, friend.user_id)
    session.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"tdr|{friend_id}"),
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"tinvite|{friend.travel_id}")
    )
    await call.message.edit_text(
        text=f"""<b>🤖 Информация о участнике путешествия</b>
        
🆔 ID: <code>{friend.user_id}</code>
📝 Имя: <b>{user.name}</b>
⚡️ Об участнике: <code>{user.bio}</code>

🗓️ Возраст: {user.age} лет
📍 Текущее местоположение: {user.country} - {user.city}""",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("tdr|"))
async def delete_friend(call: CallbackQuery):
    friend_id = int(call.data.split("|")[1])
    session = create_session(engine)
    friend = session.get(TravelMember, friend_id)
    members = session.query(TravelMember).filter_by(travel_id=friend.travel_id)
    session.delete(friend)
    session.commit()
    session.close()
    await call.answer(
        text="🗑️ Пользователь удален"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data=f"taf|{friend.travel_id}")
    )
    for member in members:
        user = session.get(User, member.user_id)
        builder.row(
            InlineKeyboardButton(text=f"#{member.id} - {user.name}", callback_data=f"tfm|{member.id}")
        )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{friend.travel_id}")
    )
    await call.message.edit_text(
        text="🤖 Список участников путешествия",
        reply_markup=builder.as_markup()
    )


