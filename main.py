import os
import json
import time
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_ID = 6712617550  # Укажи свой id
DATA_FILE = "data.json"
PHOTO_ID_FILE = "welcome_photo_id.json"
VIDEO_ID_FILE = "welcome_video_id.json"
COOLDOWN_SECONDS = 5 * 60  # 5 минут

CATEGORY_EMOJIS = {
    "Для ОПГ": "🔫"
}
CATEGORY_SECTIONS = {
    "Для ОПГ": ["bizwar"]
}
SECTION_EMOJIS = {"bizwar": "💼"}
DEFAULT_SECTION_EMOJI = "📚"

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

class Quiz(StatesGroup):
    choosing_category = State()
    choosing_section = State()
    answering = State()
    waiting_photo = State()
    waiting_video = State()

user_scores = {}
user_cooldowns = {}  # user_id: {section_id: last_time}
user_random_questions = {}  # user_id: {section_id: [индексы вопросов в рандоме]}

def load_data():
    global user_scores, user_cooldowns
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_scores.update(data.get("scores", {}))
            user_cooldowns.update(data.get("cooldowns", {}))
    else:
        user_scores.clear()
        user_cooldowns.clear()

def save_data():
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
    try:
        if os.path.exists(PHOTO_ID_FILE):
            with open(PHOTO_ID_FILE, 'r', encoding="utf-8") as f:
                d = json.load(f)
                return d.get("photo_id")
    except Exception:
        pass
    return None

def save_video_id(video_id):
    with open(VIDEO_ID_FILE, 'w', encoding="utf-8") as f:
        json.dump({"video_id": video_id}, f)

def load_video_id():
    if os.path.exists(VIDEO_ID_FILE):
        with open(VIDEO_ID_FILE, 'r', encoding="utf-8") as f:
            return json.load(f).get("video_id")
    return None

def main_menu(user_id=None):
    kb = [
        [KeyboardButton(text="📚 Разделы")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="🖼 Изменить фотографию приветствия")])
        kb.append([KeyboardButton(text="👑 Админ-меню")])
    kb.append([KeyboardButton(text="🏠 В главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def categories_menu():
    kb = [
        [KeyboardButton(text=f"{CATEGORY_EMOJIS.get(cat, '')} {cat}".strip())]
        for cat in CATEGORY_SECTIONS.keys()
    ]
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
    video_id = load_video_id()
    caption = (
        "<b>🎬 Добро пожаловать в тренажёр Black Russia!</b>\n"
        "Выбирай раздел, отвечай на вопросы, зарабатывай баллы и попадай в топ!\n\n"
        "Нажми кнопку или /menu для начала."
    )
    if video_id:
        await message.answer_video(
            video=video_id,
            caption=caption,
            reply_markup=main_menu(message.from_user.id)
        )
    else:
        await message.answer(
            caption,
            reply_markup=main_menu(message.from_user.id)
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    photo_id = load_photo_id()
    caption = "🔝 <b>Главное меню:</b>"
    if photo_id:
        await message.answer_photo(
            photo=photo_id,
            caption=caption,
            reply_markup=main_menu(message.from_user.id)
        )
    else:
        await message.answer(
            caption,
            reply_markup=main_menu(message.from_user.id)
        )

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
    category = message.text
    for emoji in CATEGORY_EMOJIS.values():
        category = category.replace(emoji, "")
    category = category.strip()
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
    section_title = message.text
    for emoji in SECTION_EMOJIS.values():
        section_title = section_title.replace(emoji, "")
    section_title = section_title.strip()
    if section_title == "⬅️ К категориям":
        await state.set_state(Quiz.choosing_category)
        await message.answer("Выберите категорию:", reply_markup=categories_menu())
        return
    if section_title == "🏠 В главное меню":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_menu(message.from_user.id))
        return
    section_ids = CATEGORY_SECTIONS[category]
    section = next((s for s in SECTIONS if s["id"] in section_ids and s["title"] == section_title), None)
    if not section:
        await message.answer("❌ Такого раздела нет.")
        return

    # КУЛДАУН!
    user_id = str(message.from_user.id)
    section_id = section["id"]
    now = int(time.time())
    last = int(user_cooldowns.get(user_id, {}).get(section_id, 0))
    wait = COOLDOWN_SECONDS - (now - last)
    if wait > 0:
        await message.answer(f"⏳ Этот раздел можно проходить раз в 5 минут.\nПодождите еще {wait//60} мин {wait%60} сек.")
        await state.clear()
        return

    # Рандомизация порядка вопросов
    q_count = len(section["questions"])
    question_order = list(range(q_count))
    random.shuffle(question_order)
    if user_id not in user_random_questions:
        user_random_questions[user_id] = {}
    user_random_questions[user_id][section_id] = question_order

    await state.update_data(section_id=section_id, q_index=0)
    await state.set_state(Quiz.answering)
    first_q_idx = question_order[0]
    q = section["questions"][first_q_idx]
    await message.answer(
        f"<b>{q['question']}</b>",
        reply_markup=question_kb(q["options"])
    )

@dp.message(Quiz.answering)
async def answer_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = str(message.from_user.id)
    section_id = data["section_id"]
    q_index = data["q_index"]
    section = next((s for s in SECTIONS if s["id"] == section_id), None)
    if not section:
        await message.answer("Ошибка раздела.")
        await state.clear()
        return

    question_order = user_random_questions.get(user_id, {}).get(section_id)
    if not question_order or q_index >= len(question_order):
        await message.answer("Ошибка вопросов. Начните раздел заново.")
        await state.clear()
        return

    q_real_idx = question_order[q_index]
    q = section["questions"][q_real_idx]
    answer = message.text.strip()
    correct = False
    try:
        correct = q["options"].index(answer) == q["answer"]
    except Exception:
        pass

    if correct:
        user_scores[user_id] = user_scores.get(user_id, 0) + 1
        save_data()
        await message.answer("✅ Верно! +1 балл")
    else:
        await message.answer(f"❌ Неверно! Правильный ответ: {q['options'][q['answer']]}")
    next_q_index = q_index + 1
    if next_q_index < len(question_order):
        await state.update_data(q_index=next_q_index)
        next_q_real_idx = question_order[next_q_index]
        next_q = section["questions"][next_q_real_idx]
        await message.answer(
            f"<b>{next_q['question']}</b>",
            reply_markup=question_kb(next_q["options"])
        )
    else:
        # выставляем кулдаун завершения раздела
        now = int(time.time())
        if user_id not in user_cooldowns:
            user_cooldowns[user_id] = {}
        user_cooldowns[user_id][section_id] = now
        save_data()
        await message.answer("Раздел пройден! Можно попытаться снова через 5 минут.", reply_markup=main_menu(message.from_user.id))
        await state.clear()
        # очищаем порядок вопросов
        user_random_questions[user_id].pop(section_id, None)

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

@dp.message(F.text == "🖼 Изменить фотографию приветствия")
async def change_photo_command(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await state.set_state(Quiz.waiting_photo)
    await message.answer("Отправь новое фото для приветствия:")

@dp.message(Quiz.waiting_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    photo_id = message.photo[-1].file_id
    save_photo_id(photo_id)
    await state.clear()
    await message.answer("Фото приветствия успешно обновлено!")

@dp.message(Command("setstartvideo"))
async def set_start_video(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await state.set_state(Quiz.waiting_video)
    await message.answer("Отправьте видео, которое будет приветствием при /start.")

@dp.message(Quiz.waiting_video, F.video)
async def handle_video(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    video_id = message.video.file_id
    save_video_id(video_id)
    await state.clear()
    await message.answer("Видео приветствия успешно сохранено.")

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Не понял команду. Жми '🏠 В главное меню' или /menu.")

load_data()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
