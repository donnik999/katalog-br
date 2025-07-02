import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from datetime import datetime, timedelta

TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_ID = 6712617550
DATA_FILE = "user_scores.json"
COOLDOWN_SEC = 3600  # 1 час

# --- ВОПРОСЫ ПО РАЗДЕЛАМ ---
SECTIONS = [
    {
        "title": "Общие вопросы",
        "id": "common",
        "questions": [
            {
                "question": "Столица России?",
                "options": ["Москва", "Сочи", "Казань", "Владивосток"],
                "answer": 0
            },
            {
                "question": "2 + 2 = ?",
                "options": ["3", "4", "5", "22"],
                "answer": 1
            },
            {
                "question": "Python — это?",
                "options": ["Язык программирования", "Река", "Птица", "Город"],
                "answer": 0
            }
        ]
    },
    {
        "title": "Числа",
        "id": "numbers",
        "questions": [
            {
                "question": "5 * 6 = ?",
                "options": ["11", "30", "56", "26"],
                "answer": 1
            },
            {
                "question": "7 + 8 = ?",
                "options": ["15", "16", "14", "13"],
                "answer": 0
            }
        ]
    }
    # Добавляй новые разделы и вопросы тут!
]

HELP_TEXT = (
    "ℹ️ <b>Помощь по боту</b>\n"
    "— Выбери 'Разделы', чтобы пройти тест из интересующей темы.\n"
    "— За каждый правильный ответ начисляются баллы.\n"
    "— После прохождения раздела действует временная задержка (кулдаун) перед повторной попыткой.\n"
    "— Посмотреть свой счёт: 'Профиль'.\n"
    "— Топ-10 игроков: 'Топ'.\n"
    "— Для вызова меню: /menu\n"
    "— Для возврата: 'В главное меню'."
)

WELCOME_TEXT = (
    "👋 <b>Добро пожаловать в тренажёр/викторину!</b>\n"
    "Выбирай раздел и проверь свои знания.\n"
    "За верные ответы получай баллы и попадай в топ игроков! 🎉"
)

PROFILE_TEMPLATE = (
    "👤 <b>Профиль</b>\n"
    "ID: <code>{user_id}</code>\n"
    "Баллы: <b>{score}</b>"
)

# --- ФСМ СОСТОЯНИЯ ---
class Quiz(StatesGroup):
    section = State()
    question = State()

# --- ГЛОБАЛЬНЫЕ ДАННЫЕ ---
user_scores = {}
user_cooldowns = {}  # {user_id: {section_id: timestamp}}

# --- СОХРАНЕНИЕ/ЗАГРУЗКА ---
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
    data = {
        "scores": user_scores,
        "cooldowns": user_cooldowns
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- КНОПКИ ---
def main_menu():
    kb = [
        [KeyboardButton(text="Разделы")],
        [KeyboardButton(text="Профиль"), KeyboardButton(text="Топ")],
        [KeyboardButton(text="Помощь")]
    ]
    if ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Админ-меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def sections_menu():
    kb = [[KeyboardButton(text=sec['title'])] for sec in SECTIONS]
    kb.append([KeyboardButton(text="⬅️ В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def question_kb(options):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=o)] for o in options], resize_keyboard=True)

def admin_menu():
    kb = [
        [KeyboardButton(text="💾 Сохранить данные")],
        [KeyboardButton(text="📝 Показать топ")],
        [KeyboardButton(text="🧹 Сбросить топ")],
        [KeyboardButton(text="⬅️ В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- БОТ ---
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

@dp.message(Command("start", "menu"))
async def start(message: types.Message, state: FSMContext):
    photo = FSInputFile("welcome.jpg") if os.path.exists("welcome.jpg") else None
    await state.clear()
    if photo:
        await message.answer_photo(photo, caption=WELCOME_TEXT, reply_markup=main_menu())
    else:
        await message.answer(WELCOME_TEXT, reply_markup=main_menu())

@dp.message(lambda m: m.text == "⬅️ В главное меню")
async def main_menu_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню.", reply_markup=main_menu())

@dp.message(lambda m: m.text == "Помощь")
async def help_cmd(message: types.Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu())

@dp.message(lambda m: m.text == "Профиль")
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    score = user_scores.get(user_id, 0)
    await message.answer(PROFILE_TEMPLATE.format(user_id=user_id, score=score), reply_markup=main_menu())

@dp.message(lambda m: m.text == "Топ")
async def top_cmd(message: types.Message):
    if not user_scores:
        await message.answer("Топ пуст.", reply_markup=main_menu())
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "<b>🏆 Топ-10 игроков:</b>\n"
    for i, (uid, score) in enumerate(top, 1):
        text += f"{i}) <code>{uid}</code> — <b>{score}</b>\n"
    await message.answer(text, reply_markup=main_menu())

@dp.message(lambda m: m.text == "Разделы")
async def sections_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выбери раздел:", reply_markup=sections_menu())

@dp.message(lambda m: any(m.text == sec['title'] for sec in SECTIONS))
async def start_section(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    section = next(sec for sec in SECTIONS if sec["title"] == message.text)
    sid = section["id"]
    now = datetime.now().timestamp()
    user_cd = user_cooldowns.get(user_id, {})
    cd = user_cd.get(sid, 0)
    if now < cd:
        left = int(cd - now)
        await message.answer(f"⏳ Повторно этот раздел можно пройти через {left//60} мин {left%60} сек", reply_markup=main_menu())
        return
    await state.set_state(Quiz.question)
    await state.update_data(sec_id=sid, q_idx=0, score=0)
    q = section["questions"][0]
    await message.answer(f"<b>Вопрос 1/{len(section['questions'])}:</b>\n{q['question']}", reply_markup=question_kb(q["options"]))

@dp.message(Quiz.question)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sec_id = data["sec_id"]
    section = next(sec for sec in SECTIONS if sec["id"] == sec_id)
    questions = section["questions"]
    q_idx = data["q_idx"]
    score = data["score"]
    q = questions[q_idx]
    user_ans = message.text.strip()
    if user_ans not in q["options"]:
        await message.answer("Пожалуйста, выбери вариант кнопкой.", reply_markup=question_kb(q["options"]))
        return
    if q["options"].index(user_ans) == q["answer"]:
        score += 1
    q_idx += 1
    if q_idx < len(questions):
        await state.update_data(q_idx=q_idx, score=score)
        q = questions[q_idx]
        await message.answer(f"<b>Вопрос {q_idx+1}/{len(questions)}:</b>\n{q['question']}", reply_markup=question_kb(q["options"]))
    else:
        user_id = str(message.from_user.id)
        user_scores[user_id] = user_scores.get(user_id, 0) + score
        cd_until = (datetime.now() + timedelta(seconds=COOLDOWN_SEC)).timestamp()
        user_cooldowns.setdefault(user_id, {})[sec_id] = cd_until
        save_scores()
        await message.answer(
            f"✅ <b>Тест окончен!</b>\nТвои баллы за раздел: <b>{score} из {len(questions)}</b>\n"
            f"Общий счёт: <b>{user_scores[user_id]}</b>\n\n"
            f"Повторно пройти этот раздел можно через 1 час.",
            reply_markup=main_menu()
        )
        await state.clear()

# --- АДМИН ---
@dp.message(lambda m: m.text == "👑 Админ-меню" and m.from_user.id == ADMIN_ID)
async def admin_menu_cmd(message: types.Message):
    await message.answer("👑 <b>Админ-меню</b>\nВыберите действие:", reply_markup=admin_menu())

@dp.message(lambda m: m.text == "💾 Сохранить данные" and m.from_user.id == ADMIN_ID)
async def admin_save(message: types.Message):
    save_scores()
    await message.answer("✅ Данные успешно сохранены.", reply_markup=admin_menu())

@dp.message(lambda m: m.text == "📝 Показать топ" and m.from_user.id == ADMIN_ID)
async def admin_show(message: types.Message):
    await top_cmd(message)

@dp.message(lambda m: m.text == "🧹 Сбросить топ" and m.from_user.id == ADMIN_ID)
async def admin_reset(message: types.Message):
    global user_scores
    user_scores = {}
    save_scores()
    await message.answer("Топ сброшен.", reply_markup=admin_menu())

# --- ОБРАБОТЧИК ВСЕГО ПРОЧЕГО ---
@dp.message()
async def fallback(message: types.Message):
    await message.answer("Не понял команду. Жми 'В главное меню' или /menu.")

# --- ЗАГРУЗКА ПРИ СТАРТЕ ---
load_scores()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
