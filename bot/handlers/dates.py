from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.filters import or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import aiosqlite


router = Router()
MAX_DATES = 10


class AddForm(StatesGroup):
    date_input = State()
    name_input = State()

class RemoveForm(StatesGroup):
    num_input = State()


def is_valid_dd_mm(date_str):
    if len(date_str) != 5:
        return False
    try:
        datetime.strptime(date_str, "%d.%m")
        return True
    except ValueError:
        return False
    

async def reset_autoincrement(user_id, db):
    await db.execute(f"""
        CREATE TABLE temp_table AS
        SELECT * FROM user_{user_id} ORDER BY id
    """)
    await db.execute(f"DROP TABLE user_{user_id}")
    await db.execute(f"""
        CREATE TABLE user_{user_id} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            name TEXT,
            UNIQUE(date, name)
        )
    """)
    await db.execute(f"""
        INSERT INTO user_{user_id} (date, name)
        SELECT date, name FROM temp_table
    """)
    await db.execute("DROP TABLE temp_table")


@router.message(StateFilter(None), or_f(
    Command("add_date"),
    F.text.lower() == 'добавить дату'
))
async def add_date(message: Message, state: FSMContext):
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(f"SELECT * FROM user_{message.from_user.id}")
        data = await cursor.fetchall()
    if len(data) < MAX_DATES:
        await message.answer(
            "Введите дату в формате дд.мм" 
        )
        await state.set_state(AddForm.date_input)
    else:
        await message.answer(
            "Достигнут лимит количества дат"
        )


@router.message(
    AddForm.date_input,
    F.text.func(is_valid_dd_mm)
)
async def input_correct_date(message: Message, state: FSMContext):
    await state.update_data(birthday_date=message.text)
    await message.answer(
        "Кто празднует День Рождения?" 
    )
    await state.set_state(AddForm.name_input)


@router.message(
    AddForm.date_input,
    F.text
)
async def input_incorrect_date(message: Message, state: FSMContext):
    await message.answer(
        "Дата не корректна" 
    )


@router.message(
    AddForm.name_input,
    F.text.len() <= 50
)
async def input_correct_name(message: Message, state: FSMContext):
    await state.update_data(birthday_name=message.text)
    user_data = await state.get_data()
    async with aiosqlite.connect("bot.db") as db:
        try:
            await db.execute(
                f"INSERT INTO user_{message.from_user.id} (date, name) VALUES (?, ?)",
                (user_data['birthday_date'], user_data['birthday_name'])
            )
            await message.answer(
                f"Добавил {user_data['birthday_date']}, {user_data['birthday_name']}" 
            )
        except aiosqlite.IntegrityError:
            await message.answer('Такая запись уже есть')
        await db.commit()
    await state.clear()


@router.message(
    AddForm.name_input,
    F.text
)
async def input_incorrect_name(message: Message, state: FSMContext):
    await message.answer(
        "Слишком длинный текст, я могу запомнить до 50 символов"
    )


@router.message(StateFilter(None), or_f(
    Command("remove_date"),
    F.text.lower() == 'удалить дату'
))
async def remove_date(message: Message, state: FSMContext):
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(f"SELECT * FROM user_{message.from_user.id}")
        data = await cursor.fetchall()
    if len(data) < 1:
        await message.answer(
            "У вас нет добавленных дат" 
        )
    else:
        await show_dates(message)
        await message.answer(
            "Отправьте порядковый номер (ID) даты для её удаления" 
        )
        await state.set_state(RemoveForm.num_input)


@router.message(
    RemoveForm.num_input,
    F.text.func(lambda text: text.isdigit() and int(text) > 0)
)
async def input_remove_num(message: Message, state: FSMContext):
    id = int(message.text)
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(f"SELECT 1 FROM user_{message.from_user.id} WHERE id = ?", (id,))
        if not await cursor.fetchone():
            await message.answer(f"Запись с ID {id} не найдена")
        else:
            await db.execute(f"DELETE FROM user_{message.from_user.id} WHERE id = ?", (id,))
            await message.answer(f"Удалил дату с ID {id}")
            await reset_autoincrement(message.from_user.id, db)
        await db.commit()
    await state.clear()


@router.message(
    RemoveForm.num_input,
    F.text
)
async def input_remove_num_incorrect(message: Message, state: FSMContext):
    await message.answer("ID должен быть целым положительным числом")


@router.message(or_f(
    Command("show_dates"),
    F.text.lower() == 'показать мои даты'
))
async def show_dates(message: Message):
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute(f"SELECT * FROM user_{message.from_user.id}")
        data = await cursor.fetchall()
    data_txt = ''
    for item in data:
        data_txt += f'<b>{item[0]}</b>. ' + ', '.join(item[1:][::-1]) + '\n'
    
    if data_txt != '':
        await message.answer(
            f"Ваши даты:\n{data_txt}",
            parse_mode='HTML'  
        )
    else:
        await message.answer(
            f"У вас нет добавленных дат",
            parse_mode='HTML'  
        )
