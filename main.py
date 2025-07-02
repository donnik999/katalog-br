import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_ID = 6712617550
DATA_FILE = "user_scores.json"
PHOTO_ID_FILE = "welcome_photo_id.json"
COOLDOWN_SEC = 300  # 5 минут

# --- ЭМОДЗИ РАЗДЕЛОВ (можно менять) ---
SECTION_EMOJIS = {
    "common": "❓",
    "numbers": "🔢"
}
DEFAULT_SECTION_EMOJI = "📦"

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
    # Добавляй новые разделы, указывай эмодзи в SECTION_EMOJIS!
]

HELP_TEXT = (
    "ℹ️ <b>Помощь по боту</b>\n"
    "— <b>Баллы</b>: За каждый правильный ответ ты получаешь 1 балл. ⚡\n"
    "— <b>Кулдаун</b>: После прохождения раздела действует задержка — повторно пройти можно через час ⏳\n"
    "— <b>Связь с автором</b>: <a href='https://t.me/bunkoc'>@bunkoc</a> (жми на ник или кнопку ниже)\n"
    "— <b>Вопросы взяты с форума игровой площадки Black Russia 🕹</b>\n"
    "\n"
    "Меню: /menu\n"
    "Вернуться: '🏠 В главное меню'"
)

WELCOME_TEXT = (
    "👋 <b>Добро пожаловать в тренажёр/викторину Black Russia!</b>\n\n"
    "Выбирай раздел и проверь свои знания из мира Black Russia.\n"
    "Правильные ответы = баллы, а лучший — в топе! 🎉"
)

PROFILE_TEMPLATE = (
    "👤 <b>Твой профиль</b>\n"
    "┏ ID: <code>{user_id}</code>\n"
    "┣ Баллы: <b>{score}</b> ⭐\n"
    "┗ Место в топе: <b>{place}</b> 🏆"
)

TOP_HEADER = "🏆 <b>Топ-10 игроков Black Russia:</b>\n"

# --- FSM СОСТОЯНИЯ ---
class Quiz(StatesGroup):
    section = State()
    question = State()
    waiting_continue = State()

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

def save_photo_id(photo_id):
    with open(PHOTO_ID_FILE, 'w', encoding="utf-8") as f:
        json.dump({"photo_id": photo_id}, f)

def load_photo_id():
    if os.path.exists(PHOTO_ID_FILE):
        with open(PHOTO_ID_FILE, 'r', encoding="utf-8") as f:
            d = json.load(f)
            return d.get("photo_id")  # безопасно!
    return None

# --- КНОПКИ ---
def main_menu():
    kb = [
        [KeyboardButton(text="📚 Разделы")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="ℹ️ Помощь")],
        [KeyboardButton(text="🖼 Изменить фотографию приветствия")] if ADMIN_ID else [],
    ]
    if ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Админ-меню")])
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=[row for row in kb if row], resize_keyboard=True)

def sections_menu():
    kb = []
    for sec in SECTIONS:
        emoji = SECTION_EMOJIS.get(sec['id'], DEFAULT_SECTION_EMOJI)
        kb.append([KeyboardButton(text=f"{emoji} {sec['title']}")])
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def question_kb(options):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=o)] for o in options], resize_keyboard=True)

def admin_menu():
    kb = [
        [KeyboardButton(text="💾 Сохранить данные")],
        [KeyboardButton(text="📝 Показать топ")],
        [KeyboardButton(text="🧹 Сбросить топ")],
        [KeyboardButton(text="🏠 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def continue_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="➡️ Продолжить")]], resize_keyboard=True)

def author_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Связаться с автором", url="https://t.me/bunkoc")]
        ]
    )

# --- БОТ ---
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- START и МЕНЮ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    photo_id = load_photo_id()
    await state.clear()
    if photo_id:
        await message.answer_photo(photo_id, caption=WELCOME_TEXT, reply_markup=main_menu())
    else:
        await message.answer(WELCOME_TEXT, reply_markup=main_menu())

@dp.message(Command("menu"))
async def menu_cmd(message: types.Message, state: FSMContext):
    photo_id = load_photo_id()
    await state.clear()
    if photo_id:
        await message.answer_photo(photo_id, caption="🏠 <b>Главное меню</b>", reply_markup=main_menu())
    else:
        await message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())

# --- ПОМОЩЬ ---
@dp.message(lambda m: m.text == "ℹ️ Помощь")
async def help_cmd(message: types.Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu(), disable_web_page_preview=True, reply_markup_markup=author_inline())

# --- ПРОФИЛЬ ---
@dp.message(lambda m: m.text == "👤 Профиль")
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    score = user_scores.get(user_id, 0)
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    place = next((i+1 for i, (uid, _) in enumerate(sorted_scores) if uid == user_id), "-")
    text = PROFILE_TEMPLATE.format(user_id=user_id, score=score, place=place)
    await message.answer(text, reply_markup=main_menu())

# --- ТОП ---
@dp.message(lambda m: m.text == "🏆 Топ")
async def top_cmd(message: types.Message):
    if not user_scores:
        await message.answer("Пока никто не набрал баллы. Будь первым!", reply_markup=main_menu())
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = TOP_HEADER
    for i, (uid, score) in enumerate(top, 1):
        text += f"{i}) <code>{uid}</code> — <b>{score}⭐</b>\n"
    await message.answer(text, reply_markup=main_menu())

# --- РАЗДЕЛЫ ---
@dp.message(lambda m: m.text == "📚 Разделы")
async def sections_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выбери раздел:", reply_markup=sections_menu())

@dp.message(lambda m: any(m.text.startswith(SECTION_EMOJIS.get(sec['id'], DEFAULT_SECTION_EMOJI)) for sec in SECTIONS))
async def start_section(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    for sec in SECTIONS:
        emoji = SECTION_EMOJIS.get(sec['id'], DEFAULT_SECTION_EMOJI)
        if message.text.startswith(emoji):
            section = sec
            break
    else:
        await message.answer("Раздел не найден.", reply_markup=main_menu())
        return
    sid = section["id"]
    now = datetime.now().timestamp()
    user_cd = user_cooldowns.get(user_id, {})
    cd = user_cd.get(sid, 0)
    if now < cd:
        left = int(cd - now)
        await message.answer(f"⏳ На этот раздел действует кулдаун! Повторно можно через {left//60} мин {left%60} сек.", reply_markup=main_menu())
        return
    await state.set_state(Quiz.question)
    await state.update_data(sec_id=sid, q_idx=0, score=0, wrong=False)
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
        await message.answer(f"✅ Верно! +1 балл", reply_markup=continue_kb())
        await state.set_state(Quiz.waiting_continue)
        await state.update_data(score=score, wrong=False)
    else:
        await message.answer(f"❌ Неверно. Правильный ответ: <b>{q['options'][q['answer']]}</b>", reply_markup=continue_kb())
        await state.set_state(Quiz.waiting_continue)
        await state.update_data(wrong=True)

@dp.message(Quiz.waiting_continue)
async def continue_after_wrong(message: types.Message, state: FSMContext):
    if message.text != "➡️ Продолжить":
        await message.answer("Нажми ➡️ Продолжить чтобы перейти к следующему вопросу.", reply_markup=continue_kb())
        return
    data = await state.get_data()
    sec_id = data["sec_id"]
    section = next(sec for sec in SECTIONS if sec["id"] == sec_id)
    questions = section["questions"]
    q_idx = data["q_idx"] + 1
    score = data["score"]
    if q_idx < len(questions):
        await state.set_state(Quiz.question)
        await state.update_data(q_idx=q_idx)
        q = questions[q_idx]
        await message.answer(f"<b>Вопрос {q_idx+1}/{len(questions)}:</b>\n{q['question']}", reply_markup=question_kb(q["options"]))
    else:
        user_id = str(message.from_user.id)
        user_scores[user_id] = user_scores.get(user_id, 0) + score
        cd_until = (datetime.now() + timedelta(seconds=COOLDOWN_SEC)).timestamp()
        user_cooldowns.setdefault(user_id, {})[sec_id] = cd_until
        save_scores()
        await message.answer(
            f"🎉 <b>Тест окончен!</b>\nТы набрал: <b>{score} из {len(questions)}</b> за этот раздел.\n"
            f"Твой общий счёт: <b>{user_scores[user_id]}⭐</b>\n\n"
            f"⏳ На этот раздел наложен кулдаун: <b>{COOLDOWN_SEC//60} минут</b>.",
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

# --- СМЕНА ФОТО ПРИВЕТСТВИЯ ---
@dp.message(lambda m: m.text == "🖼 Изменить фотографию приветствия" and m.from_user.id == ADMIN_ID)
async def change_photo_command(message: types.Message, state: FSMContext):
    await state.set_state(Quiz.section)
    await message.answer("Отправь новое фото для приветствия:")

@dp.message(Quiz.section)
async def handle_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправь именно фото!")
        return
    photo_id = message.photo[-1].file_id
    save_photo_id(photo_id)
    await message.answer_photo(photo_id, caption="Фото приветствия успешно обновлено!", reply_markup=main_menu())
    await state.clear()

# --- ОБРАБОТЧИК ВСЕГО ПРОЧЕГО ---
@dp.message()
async def fallback(message: types.Message):
    await message.answer("Не понял команду. Жми '🏠 В главное меню' или /menu.")

# --- ЗАГРУЗКА ПРИ СТАРТЕ ---
load_scores()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
