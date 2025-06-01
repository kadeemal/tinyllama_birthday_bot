from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.start_buttons import get_start_buttons
from aiogram.filters import or_f
import datetime
import aiosqlite


router = Router()
help_text = """
🤖 <b>Добро пожаловать!</b>  

Я умею напоминать о Днях Рождения и использую ИИ для генерации поздравления.  

<u>Доступные команды:</u>  

/start - Перезапустить бота  

/add_date - Добавить новую дату

/remove_date - Удалить имеющуюся дату

/show_dates - Показать имеющиеся даты

/generate_wish - Сгенерировать поздравление прямо сейчас

/help - Вывести справку по работе с ботом  

Подсказка:
Формат ввода дат: "дд.мм"
Например,
7 ноября = 07.11,
11 марта = 11.03
"""


@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    async with aiosqlite.connect("./bot.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, chat_id, last_generation) VALUES (?, ?, ?)",
            (message.from_user.id, message.chat.id, datetime.datetime(2000, 1, 1).isoformat())
        )
        await db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS user_{message.from_user.id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                name TEXT,
                UNIQUE(date, name)
            )
            """
        )
        await db.commit()
    await message.answer(help_text, parse_mode="HTML")
    await message.answer(
        "Выберите действие",
        reply_markup=get_start_buttons()
    )
    await state.clear()


@router.message(or_f(
    Command('help'),
    F.text.lower() == 'помощь'
))
async def generate_wish(message: Message):
    await message.answer(help_text, parse_mode="HTML")
