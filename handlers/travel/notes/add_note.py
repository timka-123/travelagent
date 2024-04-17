from datetime import datetime
from uuid import uuid4

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from config import config
from database import engine, Travel, TravelNote
from utils import NoteCreateStates


router = Router()


@router.callback_query(F.data.startswith("createnote"))
async def request_note_name(call: CallbackQuery, state: FSMContext):
    travel_id = int(call.data.split("|")[1])
    await state.set_state(NoteCreateStates.ENTER_NAME)
    await state.update_data(travel_id=travel_id)
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"tnotes|{travel_id}")
    )
    await call.message.edit_text(
        text="📝 Введите название заметки (не больше 24 символов)",
        reply_markup=builder.as_markup()
    )


@router.message(NoteCreateStates.ENTER_NAME)
async def request_note_content(message: Message, state: FSMContext):
    data = await state.get_data()
    travel_id = data['travel_id']
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"tnotes|{travel_id}")
    )
    if len(message.text) > 24:
        return await message.answer(
            text="❌ Название заметки не должно превышать 24 символов",
            reply_markup=builder.as_markup()
        )
    await state.set_state(NoteCreateStates.ENTER_CONTENT)
    await state.update_data(name=message.text)
    await message.answer(
        text="📝 Введите текст заметки. Также Вы можете отправить любой файл",
        reply_markup=builder.as_markup()
    )


@router.message(NoteCreateStates.ENTER_CONTENT)
async def create_travel(message: Message, state: FSMContext, bot: Bot):
    msg = await message.answer("⏳ Создаю заметку, ожидайте. Это может занять некоторое время")
    data = await state.get_data()
    has_media = False
    note_type = "text"

    if message.video:
        file = await bot.get_file(message.video.file_id)
        text = message.caption
        has_media = True
        note_type = "video"
    elif message.document:
        file = await bot.get_file(message.document.file_id)
        text = message.caption
        has_media = True
        note_type = "document"
    elif message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        text = message.caption
        has_media = True
        note_type = "photo"
    else:
        text = message.text

    session = create_session(engine)
    if has_media:
        filename = str(uuid4())
        fdata = await bot.download_file(file.file_path)
        config.s3_client.upload_fileobj(fdata, "taprod", filename)
        media_url = config.s3_baseurl + "/" + filename
        travel_note = TravelNote(
            travel_id=data['travel_id'],
            created=datetime.now(),
            content=text,
            note_type=note_type,
            file_url=media_url,
            user_id=message.from_user.id,
            name=data['name']
        )
    else:
        travel_note = TravelNote(
            travel_id=data['travel_id'],
            created=datetime.now(),
            content=text,
            note_type=note_type,
            user_id=message.from_user.id,
            name=data['name']
        )
    session.add(travel_note)
    session.commit()
    session.close()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Просмотреть", callback_data=f"noteinfo|{travel_note.id}")
    )
    await msg.delete()
    await message.answer(
        text=f"✅ Заметка создана, для просмотра нажмите на кнопку ниже",
        reply_markup=builder.as_markup()
    )
