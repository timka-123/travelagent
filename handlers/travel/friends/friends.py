from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import TravelMember, engine, User

router = Router()


@router.callback_query(F.data.startswith("tinvite"))
async def friends_callback(call: CallbackQuery, state: FSMContext):
    travel_id = int(call.data.split("|")[1])
    await state.clear()
    session = create_session(engine)
    members = session.query(TravelMember).filter_by(travel_id=travel_id)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data=f"taf|{travel_id}")
    )
    for member in members:
        user = session.get(User, member.user_id)
        builder.row(
            InlineKeyboardButton(text=f"#{member.id} - {user.name}", callback_data=f"tfm|{member.id}")
        )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{travel_id}")
    )
    await call.message.edit_text(
        text="🤖 Список участников путешествия",
        reply_markup=builder.as_markup()
    )
