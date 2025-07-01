import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

# ==== НАСТРОЙКИ БОТА ====
BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"  # <-- сюда вставь свой токен

COOLDOWN_SECONDS = 5 * 60  # 5 минут на один раздел

# ==== ВОПРОСЫ И РАЗДЕЛЫ ====
# Тут ты добавляешь новые разделы и вопросы по такому шаблону:
SECTIONS = {
    "Война за бизнес": [
        {
            "question": "Во сколько разрешено проводить войну за бизнес?",
            "answers": [
                "С 00:00 до 12:00",
                "С 12:00 до 23:00",
                "С 18:00 до 06:00",
                "В любое время"
            ],
            "correct": 1
        },
        {
            "question": "Сколько банд может находиться на бизваре одновременно?",
            "answers": [
                "1",
                "2",
                "3",
                "Без ограничений"
            ],
            "correct": 1
        }
    ],
    "Общие правила": [
        {
            "question": "Можно ли использовать читы?",
            "answers": [
                "Да",
                "Нет",
                "Только с разрешения админа",
                "Если не поймают"
            ],
            "correct": 1
        }
    ]
}
# Чтобы добавить новый раздел — копируй блок выше, меняй название и вопросы.

# ==== FSM State Machine ====
class QuizStates(StatesGroup):
    choosing_section = State()
    answering = State()

# ==== ИНИЦИАЛИЗАЦИЯ ====
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# user_id -> {section: datetime_of_last_try}
user_cooldowns = {}
# user_id -> score
user_scores = {}

# ==== КНОПКИ ====
def main_menu():
    kb = [
        [types.KeyboardButton(text="🗂 Разделы вопросов")],
        [types.KeyboardButton(text="🏆 Топ 10 игроков")],
        [types.KeyboardButton(text="ℹ️ Помощь")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def sections_menu():
    kb = [[types.KeyboardButton(text=f"📚 {section}")]
          for section in SECTIONS.keys()]
    kb.append([types.KeyboardButton(text="⬅️ В главное меню")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def answers_kb(anslist):
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=a)] for a in anslist],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выбери вариант"
    )

# ==== ХЭНДЛЕРЫ ====

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🎮 Добро пожаловать в викторину Black Russia!</b>\n"
        "Выбирай раздел, отвечай на вопросы, соревнуйся с другими!\n\n"
        "Нажми кнопку или /menu для начала.",
        reply_markup=main_menu()
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 <b>Главное меню:</b>", reply_markup=main_menu())

@dp.message(F.text == "⬅️ В главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await cmd_menu(message, state)

@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await message.answer(
        "✍️ <b>Как добавить вопросы и разделы?</b>\n"
        "1. Открой файл <code>main.py</code>.\n"
        "2. Найди переменную <code>SECTIONS</code> в начале файла.\n"
        "3. Добавь новый раздел по шаблону:\n\n"
        "<code>\"Имя раздела\": [\n"
        "  {\"question\": \"Текст вопроса\", \"answers\": [\"Вариант1\", \"Вариант2\"], \"correct\": 0},\n"
        "  ...\n"
        "]</code>\n"
        "4. Перезапусти бота.\n\n"
        "За каждый правильный ответ начисляется 1 балл.\n"
        "Можно пройти каждый раздел только 1 раз в 5 минут.\n"
        "Топ 10 игроков — кнопка в меню."
    )

@dp.message(F.text == "🗂 Разделы вопросов")
async def choose_section(message: types.Message, state: FSMContext):
    if not SECTIONS:
        await message.answer("❌ Разделы пока не добавлены.")
        return
    await state.set_state(QuizStates.choosing_section)
    await message.answer("<b>Выбери раздел для прохождения:</b>", reply_markup=sections_menu())

@dp.message(QuizStates.choosing_section)
async def section_selected(message: types.Message, state: FSMContext):
    section = message.text.replace("📚 ", "").strip()
    if section == "⬅️ В главное меню":
        await back_to_main_menu(message, state)
        return
    if section not in SECTIONS:
        await message.answer("❌ Такого раздела нет. Выбери из списка.")
        return
    # Проверка cooldown
    uid = str(message.from_user.id)
    now = datetime.utcnow()
    cooldowns = user_cooldowns.get(uid, {})
    last_time = cooldowns.get(section)
    if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
        mins = int((COOLDOWN_SECONDS - (now - last_time).total_seconds()) // 60) + 1
        await message.answer(f"⏱ Вы уже проходили этот раздел. Попробуйте снова через {mins} мин.")
        return
    questions = SECTIONS[section]
    await state.update_data(
        section=section,
        questions=questions,
        index=0,
        score=0
    )
    await ask_question(message, state)

async def ask_question(message, state: FSMContext):
    data = await state.get_data()
    idx = data["index"]
    questions = data["questions"]
    section = data["section"]
    if idx >= len(questions):
        uid = str(message.from_user.id)
        user_scores[uid] = user_scores.get(uid, 0) + data["score"]
        cooldowns = user_cooldowns.get(uid, {})
        cooldowns[section] = datetime.utcnow()
        user_cooldowns[uid] = cooldowns
        await message.answer(
            f"✅ <b>Раздел \"{section}\" завершён!</b>\n"
            f"Твои баллы: <b>{data['score']} из {len(questions)}</b>\n\n"
            f"Можешь попробовать другие разделы или посмотреть свой результат в топе.",
            reply_markup=main_menu()
        )
        await state.clear()
        return
    q = questions[idx]
    await state.set_state(QuizStates.answering)
    await state.update_data(q_current=q)
    await message.answer(
        f"<b>Вопрос {idx+1} из {len(questions)}\n\n{q['question']}</b>",
        reply_markup=answers_kb(q["answers"])
    )

@dp.message(QuizStates.answering)
async def process_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q = data["q_current"]
    idx = data["index"]
    questions = data["questions"]
    section = data["section"]
    score = data["score"]
    user_answer = message.text.strip()
    if user_answer not in q["answers"]:
        await message.answer("Пожалуйста, выбери вариант из кнопок.")
        return
    correct = q["answers"][q["correct"]]
    if user_answer == correct:
        await message.answer("✅ Верно!")
        score += 1
    else:
        await message.answer(f"❌ Неверно! Правильный ответ: <b>{correct}</b>")
    idx += 1
    await state.update_data(index=idx, score=score)
    await ask_question(message, state)

@dp.message(F.text == "🏆 Топ 10 игроков")
async def show_top(message: types.Message, state: FSMContext):
    if not user_scores:
        await message.answer("Пока нет результатов.")
        return
    top = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "<b>🏆 Топ 10 игроков по правильным ответам:</b>\n\n"
    for i, (uid, bal) in enumerate(top, 1):
        try:
            user = await bot.get_chat(uid)
            name = user.full_name if user else f"User {uid}"
        except Exception:
            name = f"User {uid}"
        text += f"{i}. <b>{name}</b> — {bal} баллов\n"
    await message.answer(text)

# === Запуск бота ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
