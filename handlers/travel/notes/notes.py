from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from database import engine, Travel, TravelNote, User
from config import config

router = Router()


@router.callback_query(F.data.startswith("tnotes"))
async def notes_list(call: CallbackQuery):
    travel_id = int(call.data.split("|")[1])
    session = create_session(engine)
    travel_notes = session.query(TravelNote).filter_by(travel_id=travel_id).all()
    session.close()

    builder = InlineKeyboardBuilder()
    for tn in travel_notes:
        builder.add(
            InlineKeyboardButton(text=f"#{tn.id} - {tn.name}", callback_data=f"noteinfo|{tn.id}")
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ Создать", callback_data=f"createnote|{travel_id}"),
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{travel_id}"),
    )
    try:
        await call.message.edit_text(
            text="📝 Ниже Вы можете увидеть список заметок к данному путешествию",
            reply_markup=builder.as_markup()
        )
    except:
        await call.message.delete()
        await call.message.answer(
            text="📝 Ниже Вы можете увидеть список заметок к данному путешествию",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("noteinfo|"))
async def show_note_info(call: CallbackQuery, state: FSMContext):
    await state.clear()
    travel_note_id = int(call.data.split("|")[1])
    session = create_session(engine)
    travel_note = session.get(TravelNote, travel_note_id)
    user = session.get(User, travel_note.user_id)
    session.close()

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Изменить название", callback_data=f"editnote|name|{travel_note_id}"),
        InlineKeyboardButton(text="📝 Изменить содержание", callback_data=f"editnote|content|{travel_note_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"editnote|delete|{travel_note_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"tnotes|{travel_note.travel_id}")
    )
    if travel_note.note_type == "text":
        await call.message.edit_text(
            text=f"""<b>📝 Информация о заметке</b>
            
🆔 ID: <code>{travel_note.id}</code>
📝 Название: <b>{travel_note.name}</b>
📝 Описание: <b>{travel_note.content}</b>

🤖 Создатель: <i>{user.name}</i>

🗓️ Дата создания: <b>{travel_note.created.strftime('%d.%m.%Y')}</b>
""",
            reply_markup=builder.as_markup()
        )
    elif travel_note.note_type == "video":
        await call.message.answer_video(
            video=URLInputFile(travel_note.file_url),
            caption=f"""<b>📝 Информация о заметке</b>
            
🆔 ID: <code>#{travel_note.id}</code>
📝 Название: <b>{travel_note.name}</b>
📝 Описание: <b>{travel_note.content}</b>

🤖 Создатель: <i>{user.name}</i>

🗓️ Дата создания: <b>{travel_note.created.strftime('%d.%m.%Y')}</b>
""",
            reply_markup=builder.as_markup()
        )
    elif travel_note.note_type == "photo":
        await call.message.answer_photo(
            photo=URLInputFile(travel_note.file_url),
            caption=f"""<b>📝 Информация о заметке</b>

🆔 ID: <code>#{travel_note.id}</code>
📝 Название: <b>{travel_note.name}</b>
📝 Описание: <b>{travel_note.content}</b>

🤖 Создатель: <i>{user.name}</i>

🗓️ Дата создания: <b>{travel_note.created.strftime('%d.%m.%Y')}</b>
        """,
            reply_markup=builder.as_markup()
        )
    elif travel_note.note_type == "document":
        await call.message.answer_document(
            document=URLInputFile(travel_note.file_url),
            caption=f"""<b>📝 Информация о заметке</b>

🆔 ID: <code>#{travel_note.id}</code>
📝 Название: <b>{travel_note.name}</b>
📝 Описание: <b>{travel_note.content}</b>

🤖 Создатель: <i>{user.name}</i>

🗓️ Дата создания: <b>{travel_note.created.strftime('%d.%m.%Y')}</b>
                """,
            reply_markup=builder.as_markup()
        )
