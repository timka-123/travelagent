from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session
from aiogram.fsm.context import FSMContext

from database import engine, User
from .onboarding.registration import request_name

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    session = create_session(engine)
    user = session.get(User, message.from_user.id)
    session.close()
    if user:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ Создать путешествие", callback_data="createtravel")
        )
        builder.row(
            InlineKeyboardButton(text="✈️ Путешествия", callback_data="travels"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        )
        await message.answer(
            text="🏡 Вы находитесь в главном меню",
            reply_markup=builder.as_markup()
        )
    else:
        await request_name(message, state)


@router.callback_query(F.data.startswith("home"))
async def home_button(call: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Создать путешествие", callback_data="createtravel")
    )
    builder.row(
        InlineKeyboardButton(text="✈️ Путешествия", callback_data="travels"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
    )
    await call.message.edit_text(
        text="🏡 Вы находитесь в главном меню",
        reply_markup=builder.as_markup()
    )
