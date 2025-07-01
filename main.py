import logging
import random
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import asyncio

API_TOKEN = '7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU'  # <-- Укажи свой токен

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Категории и вопросы
CATEGORIES = {
    "ПДД": [
        {"question": "Какова максимальная скорость в городе по правилам Black Russia?", "answer": "60 км/ч"},
        {"question": "Можно ли обгонять на сплошной линии?", "answer": "Нет"}
    ],
    "RP команды": [
        {"question": "Что означает команда /me в RP отыгровке?", "answer": "Описание действий персонажа"},
        {"question": "Для чего используется /do?", "answer": "Описание окружающей обстановки"}
    ],
    "Арест / полиция": [
        {"question": "Что делать при аресте сотрудником полиции?", "answer": "Подчиниться требованиям и отыгрывать RP"},
        {"question": "Можно ли скрываться от ареста без отыгровки?", "answer": "Нет"}
    ]
}

user_stats = {}
user_current_question = {}
user_current_category = {}

# Старт / помощь
@router.message(Command("start", "help"))
async def start_handler(message: Message):
    text = (
        "👋 Привет! Я RP тренажер для Black Russia.\n"
        "Твой помощник: @bunkoc / @tunkoc\n"
        "Напиши /quiz чтобы начать тест.\n"
        "Напиши /top чтобы посмотреть топ игроков."
    )
    await message.answer(text)

# Кнопки категорий
def get_category_keyboard():
    buttons = [
        [InlineKeyboardButton(text=cat, callback_data=f"category:{cat}")]
        for cat in CATEGORIES.keys()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Запуск викторины
@router.message(Command("quiz"))
async def quiz_handler(message: Message):
    await message.answer("Выбери категорию:", reply_markup=get_category_keyboard())

# Обработка выбора категории
@router.callback_query(lambda c: c.data.startswith("category:"))
async def category_selected(callback: types.CallbackQuery):
    cat = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user_current_category[user_id] = cat
    user_stats.setdefault(user_id, {"correct": 0, "total": 0})
    await callback.message.edit_text(f"📌 Категория выбрана: <b>{cat}</b>")
    await send_new_question(user_id)

# Кнопки для ответа
def get_answer_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать ответ", callback_data="show_answer")]
        ]
    )

async def send_new_question(user_id):
    category = user_current_category[user_id]
    question = random.choice(CATEGORIES[category])
    user_current_question[user_id] = question
    await bot.send_message(
        user_id,
        f"❓ <b>{question['question']}</b>",
        reply_markup=get_answer_keyboard()
    )

# Пользовательский ответ
@router.message()
async def user_reply_handler(message: Message):
    user_id = message.from_user.id
    if user_id not in user_current_question:
        await message.answer("Сначала выбери категорию через /quiz.")
        return

    question = user_current_question[user_id]
    correct_answer = question["answer"].lower()
    user_answer = message.text.lower()

    user_stats[user_id]["total"] += 1

    if len(correct_answer.split()) > 3 and correct_answer == user_answer:
        await message.answer("🤔 Ваш ответ слишком похож на текст с форума. Попробуйте своими словами!")
        return

    if user_answer == correct_answer:
        user_stats[user_id]["correct"] += 1
        await message.answer("✅ Верно!")
    else:
        await message.answer(f"❌ Неверно.\nПравильный ответ: <b>{question['answer']}</b>")

    await send_new_question(user_id)

# Показать ответ
@router.callback_query(lambda c: c.data == "show_answer")
async def show_answer_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_current_question:
        await callback.answer("Начните тест с /quiz")
        return

    question = user_current_question[user_id]
    user_stats[user_id]["total"] += 1
    await callback.message.answer(f"📌 Правильный ответ: <b>{question['answer']}</b>")
    await send_new_question(user_id)

# Топ пользователей
@router.message(Command("top"))
async def top_handler(message: Message):
    if not user_stats:
        await message.answer("Топ пуст. Никто не начал тест.")
        return

    sorted_users = sorted(
        user_stats.items(),
        key=lambda x: x[1]["correct"],
        reverse=True
    )
    text = "<b>🏆 Топ пользователей:</b>\n"
    for i, (uid, stats) in enumerate(sorted_users[:10], 1):
        name = f"ID:{uid}"
        text += f"{i}. {name} — {stats['correct']} баллов\n"

    await message.answer(text)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
