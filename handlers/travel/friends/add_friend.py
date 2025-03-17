from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message, switch_inline_query_chosen_chat
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from utils import AddFriendsStates
from database import engine, TravelMember, User, Travel

router = Router()


@router.callback_query(F.data.startswith("taf"))
async def request_contact(call: CallbackQuery, state: FSMContext):
    travel_id = int(call.data.split("|")[1])
    await state.set_state(AddFriendsStates.ENTER_CONTACT)
    builder = InlineKeyboardBuilder()
    query = f"jointravel-{travel_id}"
    builder.add(
        InlineKeyboardButton(text="💠 Отправить", switch_inline_query_chosen_chat=switch_inline_query_chosen_chat.SwitchInlineQueryChosenChat(
            query=f"https://t.me/T_TravelAgentBot?start={query} <- Перейди по этой ссылке, чтобы присоединиться к моему путешествию!",
            allow_user_chats=True,
            allow_group_chats=True,
            allow_channel_chats=False,
            allow_bot_chats=False
        ))
    )
    await state.update_data(travel_id=travel_id)
    await call.message.answer(
        text="📇 Нажмите на кнопку ниже, чтобы отправить инвайт другу!",
        reply_markup=builder.as_markup()
    )


@router.message(AddFriendsStates.ENTER_CONTACT)
async def add_friend(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    travel_id = data['travel_id']
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"tinvite|{travel_id}")
    )
    if not message.contact:
        return await message.answer(
            text="❌ Вы отправили не контакт, а что-то другое. Вам нужно отправить контакт пользователя, которого "
                 "хотите добавить (скрепка - отправить контакт)",
            reply_markup=builder.as_markup()
        )

    session = create_session(engine)
    user = session.get(User, message.contact.user_id)
    if not user:
        return await message.answer(
            text="❌ Не смог найти пользователя в базе данных. Запустил ли он бота?",
            reply_markup=builder.as_markup()
        )

    travel_member = session.query(TravelMember).filter_by(user_id=message.contact.user_id).filter_by(travel_id=travel_id).first()
    if travel_member:
        return await message.answer(
            text="❌ Пользователь уже добавлен в путешествие",
            reply_markup=builder.as_markup()
        )

    travel_member = TravelMember(
        user_id=message.contact.user_id,
        travel_id=travel_id
    )
    travel = session.get(Travel, travel_id)
    session.add(travel_member)
    session.commit()
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🤖 Управление участником", callback_data=f"tfm|{travel_member.id}")
    )
    await message.answer(
        text="✅ Участник добавлен!",
        reply_markup=builder.as_markup()
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
