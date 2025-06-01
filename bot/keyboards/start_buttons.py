from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_start_buttons() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Добавить дату")
    kb.button(text="Удалить дату")
    kb.button(text="Сгенерировать пожелание")
    kb.button(text="Показать мои даты")
    kb.button(text="Помощь")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)
