import logging
from aiogram import Bot, Dispatcher, types, executor
import random
import asyncio

API_TOKEN = '7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU'  # <-- Вставь свой токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Вопросы по категориям
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

# /start
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        f"Привет! Я RP тренажер для Black Russia.\n"
        f"Твой помощник: @bunkoc / @tunkoc\n"
        f"Напиши /quiz чтобы начать тест."
    )

# /quiz — выбор категории
@dp.message_handler(commands=['quiz'])
async def select_category(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES.keys():
        markup.add(cat)
    await message.reply("Выбери категорию:", reply_markup=markup)

# Категория выбрана
@dp.message_handler(lambda message: message.text in CATEGORIES)
async def start_category_quiz(message: types.Message):
    user_id = message.from_user.id
    category = message.text
    user_current_category[user_id] = category
    user_stats[user_id] = {"correct": 0, "total": 0}
    await send_new_question(user_id)

async def send_new_question(user_id):
    category = user_current_category[user_id]
    question = random.choice(CATEGORIES[category])
    user_current_question[user_id] = question
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Показать ответ")
    await bot.send_message(
        user_id,
        f"❓ [{category}] Вопрос:\n{question['question']}",
        reply_markup=markup
    )

# Обработка ответа
@dp.message_handler(lambda message: True)
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_current_question:
        await message.reply("Сначала выбери категорию с помощью /quiz.")
        return

    question = user_current_question[user_id]
    correct_answer = question['answer'].lower()
    user_reply = message.text.lower()

    if user_reply == "показать ответ":
        await message.reply(f"✅ Правильный ответ: {question['answer']}")
        user_stats[user_id]["total"] += 1
        await send_new_question(user_id)
        return

    user_stats[user_id]["total"] += 1

    if len(correct_answer.split()) > 3 and correct_answer == user_reply:
        await message.reply("🤔 Ваш ответ слишком похож на текст с форума. Попробуйте своими словами!")
        return

    if correct_answer == user_reply:
        user_stats[user_id]["correct"] += 1
        await message.reply("🎯 Верно!")
    else:
        await message.reply(f"❌ Неверно.\nПравильный ответ: {question['answer']}")

    await send_new_question(user_id)

# /stats — статистика
@dp.message_handler(commands=['stats'])
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    stats = user_stats.get(user_id)
    if not stats:
        await message.reply("Нет данных. Начни с /quiz.")
        return
    await message.reply(f"📊 Статистика:\nПравильных: {stats['correct']} из {stats['total']}")
