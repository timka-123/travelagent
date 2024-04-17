from uuid import uuid4

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import create_session

from config import config
from database import engine, TravelNote, User
from utils import NoteEditStates

router = Router()


@router.callback_query(F.data.startswith("editnote|"))
async def edit_note(call: CallbackQuery, state: FSMContext):
    cnd, action, note_id = call.data.split("|")
    session = create_session(engine)
    note = session.get(TravelNote, note_id)
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"noteinfo|{note.id}")
    )
    await state.set_state(NoteEditStates.ENTER_NEW_DATA)
    await state.update_data(note_id=note_id)

    if action == "delete":
        session.delete(note)
        session.commit()
        travel_notes = session.query(TravelNote).filter_by(travel_id=note.travel_id).all()
        session.close()

        cancel_builder = InlineKeyboardBuilder()
        for tn in travel_notes:
            cancel_builder.add(
                InlineKeyboardButton(text=f"#{tn.id} - {tn.name}", callback_data=f"noteinfo|{tn.id}")
            )
        cancel_builder.adjust(2)
        cancel_builder.row(
            InlineKeyboardButton(text="➕ Создать", callback_data=f"createnote|{note.travel_id}"),
            InlineKeyboardButton(text="🏡 Обратно", callback_data=f"travel|{note.travel_id}"),
        )
        await call.answer("🗑️ Удалено")
        await call.message.delete()
        return await call.message.answer(
            text="📝 Ниже Вы можете увидеть список заметок к данному путешествию",
            reply_markup=cancel_builder.as_markup()
        )
    elif action == "name":
        await state.update_data(action="name")
        await call.message.delete()
        await call.message.answer(
            text=f"📝 Введите новое название",
            reply_markup=builder.as_markup()
        )
    elif action == "content":
        await state.update_data(action="content")
        await call.message.delete()
        await call.message.answer(
            text=f"📝 Введите новое содержание заметки",
            reply_markup=builder.as_markup()
        )


@router.message(NoteEditStates.ENTER_NEW_DATA)
async def apply_changes(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    session = create_session(engine)
    note = session.get(TravelNote, data['note_id'])

    if data['action'] == "name":
        note.name = message.text
        session.commit()
        session.close()
    elif data['action'] == "content":
        has_media = False
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
        if has_media:
            filename = str(uuid4())
            fdata = await bot.download_file(file.file_path)
            config.s3_client.upload_fileobj(fdata, "taprod", filename)
            media_url = config.s3_baseurl + "/" + filename
            note.note_type = note_type
            note.content = text
            note.file_url = media_url
            session.commit()
        else:
            note.content = text
            session.commit()
        session.close()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Изменить название", callback_data=f"editnote|name|{note.id}"),
        InlineKeyboardButton(text="📝 Изменить содержание", callback_data=f"editnote|content|{note.id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"editnote|delete|{note.id}")
    )
    builder.row(
        InlineKeyboardButton(text="🏡 Обратно", callback_data=f"tnotes|{note.travel_id}")
    )
    travel_note = note
    user = session.get(User, message.from_user.id)
    if travel_note.note_type == "text":
        await message.answer(
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
        await message.answer_video(
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
        await message.answer_photo(
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
        await message.answer_document(
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
