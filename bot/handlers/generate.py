from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from model import inference
from aiogram.filters import or_f
import aiosqlite
from datetime import datetime


router = Router()
model_path = "./tinyllama/merged"
model, tokenizer = inference.prepare_merged_model_and_tokenizer(model_path)
prompt = "### Instruction: Напиши подравление c Днем Рождения"
model.eval() 


def generate():
    response = inference.generate_response(model, tokenizer, prompt)
    response = response.split('### Response: ')[-1]
    return response


@router.message(or_f(
    Command("generate_wish"),
    F.text.lower() == 'сгенерировать пожелание'
))
async def generate_wish(message: Message):
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
        user_id, _, last_generate = await cursor.fetchone()

    now = datetime.now()
    seconds_diff = (now - datetime.fromisoformat(last_generate)).total_seconds()

    if seconds_diff > 60:
        async with aiosqlite.connect("bot.db") as db:
            await db.execute(
                "UPDATE users SET last_generation = ? WHERE user_id = ?",
                (now.isoformat(), user_id)
            )
            await db.commit()
        await message.answer('Генерирую...')
        await message.answer(generate())

    else:
        await message.answer(
            "В целях безопасности бота генерация ограничена.\n" \
            "Вы можете генерировать не чаще, чем 1 раз в 60 секунд."
        )
