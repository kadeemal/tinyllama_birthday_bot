import os
import asyncio
import aiosqlite
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import BotCommand
from bot.handlers import start, generate, dates
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


async def birthday_wish(bot: Bot):
    async with aiosqlite.connect("./bot.db") as db:
        cursor = await db.execute("SELECT * FROM users")
        data = await cursor.fetchall()

    today = datetime.today().strftime("%d.%m")
    for user_id, chat_id, _ in data:
        async with aiosqlite.connect("./bot.db") as db:
            cursor = await db.execute(f"SELECT * FROM user_{user_id} WHERE date = ?", (today,))
            user_data = await cursor.fetchall()

        for _, _, name in user_data:
            wish = f"{name} сегодня празднует День Рождения! Не забудьте поздравить!\n\n"
            wish += "Текст поздравления:\n"
            wish += generate.generate()
            await bot.send_message(chat_id=chat_id, text=wish)


async def db_init():
    async with aiosqlite.connect("./bot.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            last_generation TEXT
        )
        """)
        await db.commit()


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="generate_wish", description="Сгенерировать пожелание"),
        BotCommand(command="add_date", description="Добавить дату"),
        BotCommand(command="remove_date", description="Удалить дату"),
        BotCommand(command="show_dates", description="Показать мои даты"),
        BotCommand(command="help", description="Помощь")
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()

    dp.include_router(start.router)
    dp.include_router(generate.router)
    dp.include_router(dates.router)
    dp.startup.register(db_init)

    scheduler.add_job(
        birthday_wish,
        trigger=CronTrigger(hour=7, minute=0),
        kwargs={'bot': bot}
    )
    scheduler.start()

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
