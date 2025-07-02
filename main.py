import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_ID = 6712617550
DATA_FILE = "user_scores.json"
COOLDOWN_SEC = 3600  # 1 час

# --- ШАБЛОНЫ ВОПРОСОВ (пример) ---
QUESTIONS = [
    {
        "question": "Столица России?",
        "options": ["Москва", "Питер", "Казань", "Владивосток"],
        "answer": 0
    },
    {
        "question": "2+2?",
        "options": ["3", "4", "5", "22"],
        "answer": 1
    },
    {
        "question": "Python — это?",
        "options": ["Язык программирования", "Река", "Птица", "Город"],
        "answer": 0
    }
    # Добавь свои вопросы тут!
]

# --- СОСТОЯНИЯ ---
class Quiz(StatesGroup):
    question = State()

# --- ГЛОБАЛЬНЫЕ ДАННЫЕ ---
user_scores = {}
user_cooldowns = {}  # user_id: timestamp

# --- ФУНКЦИИ СОХРАНЕНИЯ/ЗАГРУЗКИ ---
def load_scores():
    global user_scores, user_cooldowns
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            user_scores = data.get("scores", {})
            user_cooldowns = data.get("cooldowns", {})
    else:
        user_scores = {}
        user_cooldowns = {}

def save_scores():
    data = {
        "scores": user_scores,
        "cooldowns": user_cooldowns
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- КНОПКИ ---
def main_menu():
    kb = [[KeyboardButton(text="Начать тест")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_menu():
    kb = [
        [KeyboardButton(text="💾 Сохранить данные")],
        [KeyboardButton(text="📝 Показать данные")],
        [KeyboardButton(text="⬅️ В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- БОТ ---
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Жми 'Начать тест' чтобы начать.", reply_markup=main_menu())

@dp.message(lambda m: m.text == "Начать тест")
async def start_quiz(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    now = datetime.now().timestamp()
    cd = user_cooldowns.get(user_id, 0)
    if now < cd:
        left = int(cd - now)
        await message.answer(f"Можно проходить тест раз в час! Осталось: {left//60} мин {left%60} сек")
        return
    await state.set_state(Quiz.question)
    await state.update_data(q_idx=0, score=0)
    await send_question(message, state, 0)

async def send_question(message, state, idx):
    q = QUESTIONS[idx]
    kb = [[KeyboardButton(text=opt)] for opt in q["options"]]
    await message.answer(
        f"Вопрос {idx+1}/{len(QUESTIONS)}:\n{q['question']}",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )

@dp.message(Quiz.question)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idx = data["q_idx"]
    score = data["score"]
    q = QUESTIONS[idx]
    user_ans = message.text.strip()
    if user_ans not in q["options"]:
        await message.answer("Пожалуйста, выбери вариант кнопкой.")
        return
    if q["options"].index(user_ans) == q["answer"]:
        score += 1
    idx += 1
    if idx < len(QUESTIONS):
        await state.update_data(q_idx=idx, score=score)
        await send_question(message, state, idx)
    else:
        user_id = str(message.from_user.id)
        user_scores[user_id] = score
        user_cooldowns[user_id] = (datetime.now() + timedelta(seconds=COOLDOWN_SEC)).timestamp()
        save_scores()
        await message.answer(f"Тест окончен!\nТы набрал: {score} из {len(QUESTIONS)}",
                             reply_markup=main_menu())
        await message.answer("Возвращаю в главное меню.")
        await state.clear()

@dp.message(lambda m: m.text == "Админ-панель" and m.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.answer("👑 Админ-панель\nВыберите действие:", reply_markup=admin_menu())

@dp.message(lambda m: m.text == "💾 Сохранить данные" and m.from_user.id == ADMIN_ID)
async def admin_save(message: types.Message):
    save_scores()
    await message.answer("Данные пользователей успешно сохранены!", reply_markup=admin_menu())

@dp.message(lambda m: m.text == "📝 Показать данные" and m.from_user.id == ADMIN_ID)
async def admin_show(message: types.Message):
    await message.answer(f"<code>{json.dumps(user_scores, indent=2, ensure_ascii=False)}</code>", parse_mode="HTML")

@dp.message(lambda m: m.text == "⬅️ В главное меню")
async def to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню.", reply_markup=main_menu())

@dp.message()
async def fallback(message: types.Message):
    if message.from_user.id == ADMIN_ID and message.text.lower() == "админ-панель":
        await admin_panel(message)
    else:
        await message.answer("Не понял команду. Жми /start.")

# --- АВТОЗАГРУЗКА ДАННЫХ ---
load_scores()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
