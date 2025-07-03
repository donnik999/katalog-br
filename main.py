import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_ID = 6712617550  # Укажи свой id
DATA_FILE = "data.json"

# --- Категории и разделы ---
CATEGORY_SECTIONS = {
    "Для ОПГ": ["bizwar"]
}

SECTIONS = [
    {
        "title": "Правила войны за бизнес (БизВар)",
        "id": "bizwar",
        "questions": [
            {
                "question": "В какое время разрешено проводить Войну за бизнес?",
                "options": ["С 12:00 по 20:00", "В любое время", "С 12:00 до 23:00", "С 10:00 до 18:00"],
                "answer": 2
            },
            {
                "question": "Какое количество участников возможно при войне за бизнес?",
                "options": ["Любое количество", "От 5 до 15", "Только 5", "Не меньше 20"],
                "answer": 1
            },
            {
                "question": "Какой промежуток между проведением войны за бизнес?",
                "options": ["15 минут", "1 час", "Нет промежутков", "2 часа"],
                "answer": 3
            },
            {
                "question": "Какое количество ОПГ возможно при войне за бизнес?",
                "options": ["Любое количество", "Могут все 3", "Только 2"],
                "answer": 2
            },
            {
                "question": "В какие дни разрешено проводить Бизвары (Без обоюдного согласия)",
                "options": ["Понедельник/Среда/Пятница/Суббота", "В любой день", "Вторник/Четверг/Воскресенье", "Только в субботу"],
                "answer": 0
            },
            {
                "question": "Какое количество раз ОПГ может забивать стрелу другой ОПГ за день?",
                "options": ["Любое количество", "Не меньше 2", "Только 4", "Только 1"],
                "answer": 2
            },
            {
                "question": "Разрешено ли использование аптечки при войне за бизнес?",
                "options": ["Да, даже во время перестрелки", "Категорически запрещено", "Разрешено, но только в укрытии"],
                "answer": 2
            },
            {
                "question": "В какое время следует вводить команду /bizwar?",
                "options": ["В любое время", "Строго за 30 минут до начала Бизвара", "В хх:15", "В хх:55"],
                "answer": 1
            },
            {
                "question": "Разрешено ли использование масок во время войны за бизнес?",
                "options": ["Да, без всяких причин", "Да, но только в укрытии", "Категорически запрещено", "Если разрешит админ"],
                "answer": 2
            },
            {
                "question": "Разрешено ли сбивать темп стрельбы во время Бизвара?",
                "options": ["Да, если согласовано с другим ОПГ", "Категорически запрещено", "Можно в любом случае"],
                "answer": 0
            }
        ]
    }
]

SECTION_EMOJIS = {"bizwar": "💼"}
DEFAULT_SECTION_EMOJI = "📚"

# --- FSM States ---
class Quiz(StatesGroup):
    choosing_category = State()
    choosing_section = State()
    answering = State()

user_scores = {}
user_cooldowns = {}

def load_scores():
    global user_scores, user_cooldowns
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_scores = data.get("scores", {})
            user_cooldowns = data.get("cooldowns", {})
    else:
        user_scores = {}
        user_cooldowns = {}

def save_scores():
    data = {"scores": user_scores, "cooldowns": user_cooldowns}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_menu(user_id=None):
    kb = [
        [KeyboardButton(text="📚 Разделы")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Админ-меню")])
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def categories_menu():
    kb = [[KeyboardButton(text=cat)] for cat in CATEGORY_SECTIONS.keys()]
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def sections_menu(category):
    kb = []
    section_ids = CATEGORY_SECTIONS[category]
    for sec_id in section_ids:
        section = next((s for s in SECTIONS if s["id"] == sec_id), None)
        if section:
            emoji = SECTION_EMOJIS.get(sec_id, DEFAULT_SECTION_EMOJI)
            kb.append([KeyboardButton(text=f"{emoji} {section['title']}")])
    kb.append([KeyboardButton(text="⬅️ К категориям")])
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def question_kb(options):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=o)] for o in options], resize_keyboard=True)

bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🎮 Добро пожаловать! Жми /menu или кнопку ниже для старта.</b>",
        reply_markup=main_menu(message.from_user.id)
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 <b>Главное меню:</b>", reply_markup=main_menu(message.from_user.id))

@dp.message(F.text == "🏠 В главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await cmd_menu(message, state)

@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await message.answer(
        "<b>🕹 Помощь</b>\nВыбирай раздел, отвечай на вопросы, зарабатывай баллы и попадай в топ!"
    )

@dp.message(F.text == "📚 Разделы")
async def choose_category(message: types.Message, state: FSMContext):
    await state.set_state(Quiz.choosing_category)
    await message.answer("<b>Выберите категорию:</b>", reply_markup=categories_menu())

@dp.message(Quiz.choosing_category)
async def category_selected(message: types.Message, state: FSMContext):
    category = message.text.strip()
    if category == "🏠 В главное меню":
        await message.answer("Вы в главном меню.", reply_markup=main_menu(message.from_user.id))
        await state.clear()
        return
    if category not in CATEGORY_SECTIONS:
        await message.answer("❌ Такой категории нет. Выберите категорию из списка.")
        return
    await state.update_data(category=category)
    await state.set_state(Quiz.choosing_section)
    await message.answer(
        f"<b>Вы выбрали категорию:</b> {category}\n\nВыберите раздел:",
        reply_markup=sections_menu(category)
    )

@dp.message(Quiz.choosing_section)
async def section_selected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    if message.text == "⬅️ К категориям":
        await state.set_state(Quiz.choosing_category)
        await message.answer("Выберите категорию:", reply_markup=categories_menu())
        return
    if message.text == "🏠 В главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_menu(message.from_user.id))
        return
    # Убираем эмодзи
    section_title = message.text
    for emoji in SECTION_EMOJIS.values():
        section_title = section_title.replace(emoji, "")
    section_title = section_title.strip()
    section_ids = CATEGORY_SECTIONS[category]
    section = next((s for s in SECTIONS if s["id"] in section_ids and s["title"] == section_title), None)
    if not section:
        await message.answer("❌ Такого раздела нет.")
        return
    await state.update_data(section_id=section["id"], q_index=0)
    await state.set_state(Quiz.answering)
    q = section["questions"][0]
    await message.answer(
        f"<b>{q['question']}</b>",
        reply_markup=question_kb(q["options"])
    )

@dp.message(Quiz.answering)
async def answer_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    section_id = data["section_id"]
    q_index = data["q_index"]
    section = next((s for s in SECTIONS if s["id"] == section_id), None)
    if not section:
        await message.answer("Ошибка раздела.")
        await state.clear()
        return
    q = section["questions"][q_index]
    answer = message.text.strip()
    correct = False
    try:
        correct = q["options"].index(answer) == q["answer"]
    except Exception:
        pass
    if correct:
        await message.answer("✅ Верно!")
        # Тут начисляй баллы, если нужно
    else:
        await message.answer(f"❌ Неверно! Правильный ответ: {q['options'][q['answer']]}")
    if q_index + 1 < len(section["questions"]):
        await state.update_data(q_index=q_index + 1)
        next_q = section["questions"][q_index + 1]
        await message.answer(
            f"<b>{next_q['question']}</b>",
            reply_markup=question_kb(next_q["options"])
        )
    else:
        await message.answer("Раздел пройден!", reply_markup=main_menu(message.from_user.id))
        await state.clear()

@dp.message(F.text == "👤 Профиль")
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    score = user_scores.get(user_id, 0)
    text = (
        f"👤 <b>Твой профиль</b>\n"
        f"┏ ID: <code>{user_id}</code>\n"
        f"┣ Баллы: <b>{score}</b> ⭐\n"
    )
    await message.answer(text, reply_markup=main_menu(message.from_user.id))

@dp.message(F.text == "🏆 Топ")
async def top_cmd(message: types.Message):
    if not user_scores:
        await message.answer("Пока никто не набрал баллы. Будь первым!", reply_markup=main_menu(message.from_user.id))
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 <b>Топ-10 пользователей данного бота:</b>\n"
    for i, (uid, score) in enumerate(top, 1):
        text += f"{i}) <code>{uid}</code> — <b>{score}⭐</b>\n"
    await message.answer(text, reply_markup=main_menu(message.from_user.id))

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Не понял команду. Жми '🏠 В главное меню' или /menu.")

load_scores()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
