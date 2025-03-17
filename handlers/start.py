from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session
from aiogram.fsm.context import FSMContext

from database import engine, User, Travel, TravelMember
from .onboarding.registration import request_name

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, bot):
    session = create_session(engine)
    user = session.get(User, message.from_user.id)
    travel_id = -1
    session.close()

    try:
        _, travel = message.text.split()
        travel_id = travel.split("-")[1]
        await state.update_data(travel_id=travel_id)
    except:
        ...

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

        if travel_id != -1:
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

    else:
        if travel_id != -1:
            await message.answer("Вас пригласили в путешествие, но нужно пройти несколько шагов. Пожалуйста, сделайте это")
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
