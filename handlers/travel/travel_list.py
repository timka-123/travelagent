from typing import List, Type
from math import ceil
from logging import error

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, Travel, TravelMember

router = Router()


async def send_travels(call: CallbackQuery, travels: List[Type[Travel]], page_number: int, index: int):
    if not travels:
        return await call.answer(
            text="❌ У вас еще нет путешествий",
            show_alert=False
        )
    builder = InlineKeyboardBuilder()
    for i in range(index, index + 4):
        try:
            travel = travels[i]
            builder.row(InlineKeyboardButton(
                        text=f"#{travel.id} - {travel.name}",
                        callback_data=f"travel|{travel.id}"
                    ))
        except IndexError:
            ...        
    builder.row(
        InlineKeyboardButton(text="⬅️", callback_data=f"travelpaginated|{index - 4}|{page_number - 1}"),
        InlineKeyboardButton(text=str(page_number), callback_data="pass"),
        InlineKeyboardButton(text="➡️", callback_data=f"travelpaginated|{index + 4}|{page_number + 1}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data="home")
    )
    try:
        await call.message.edit_text(
            text="✈️ Ниже представлен ваш список путешествий",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        error(e)
        return await call.answer("❌ Произошла ошибка при пагинации")


@router.callback_query(F.data == "travels")
async def list_travels(call: CallbackQuery):
    session = create_session(engine)
    query = session.query(Travel)
    travels = query.filter_by(user=call.from_user.id).all()
    me_at_other = session.query(TravelMember).filter_by(user_id=call.from_user.id).all()
    other_travels = []
    for mao in me_at_other:
        other_travels.append(
            session.get(Travel, mao.travel_id)
        )
    session.close()
    travels += other_travels
    await send_travels(call, travels, index=0, page_number=1)


@router.callback_query(F.data.startswith("travelpaginated"))
async def paginate_travel(call: CallbackQuery):
    index = int(call.data.split('|')[1])
    page_number = int(call.data.split("|")[2])
    if index < 0:
        index = 0
    session = create_session(engine)
    query = session.query(Travel)
    travels = query.filter_by(user=call.from_user.id).all()
    me_at_other = session.query(TravelMember).filter_by(user_id=call.from_user.id).all()
    other_travels = []
    for mao in me_at_other:
        other_travels.append(
            session.get(Travel, mao.travel_id)
        )
    session.close()
    travels += other_travels
    if index > len(travels):
        return await call.answer(
            text="❌ Это была последняя страница"
        )   
    session.close()     
    await send_travels(call, travels, index=index, page_number=page_number)
