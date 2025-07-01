import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"

QUESTIONS_PATH = "data/questions.json"
COOLDOWN_SECONDS = 5 * 60  # 5 минут

if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(QUESTIONS_PATH):
    with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def load_questions():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_questions(qdata):
    with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(qdata, f, ensure_ascii=False, indent=2)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# user_id -> {раздел: time_of_last_try, ...}
user_cooldowns = {}

# user_id -> score
user_scores = {}

class QuizStates(StatesGroup):
    choosing_section = State()
    answering = State()

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🎮 Добро пожаловать в викторину Black Russia!</b>\n\n"
        "❓ Выбирай раздел, отвечай на вопросы, соревнуйся с другими!",
        reply_markup=main_menu()
    )

def main_menu():
    kb = [
        [types.KeyboardButton("🗂 Разделы вопросов")],
        [types.KeyboardButton("🏆 Топ 10 игроков")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def sections_menu(qdata):
    kb = [[types.KeyboardButton(text=f"📚 {section}")] for section in qdata]
    kb.append([types.KeyboardButton(text="⬅️ В главное меню")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def answers_kb(anslist):
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=a)] for a in anslist],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выбери вариант"
    )

@dp.message(F.text == "⬅️ В главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 <b>Главное меню:</b>", reply_markup=main_menu())

@dp.message(F.text == "🗂 Разделы вопросов")
async def choose_section(message: types.Message, state: FSMContext):
    qdata = load_questions()
    if not qdata:
        await message.answer("Разделы пока не добавлены.")
        return
    await state.set_state(QuizStates.choosing_section)
    await message.answer("<b>Выбери раздел для прохождения:</b>", reply_markup=sections_menu(qdata))

@dp.message(QuizStates.choosing_section)
async def section_selected(message: types.Message, state: FSMContext):
    section = message.text.replace("📚 ", "")
    qdata = load_questions()
    if section == "В главное меню" or section == "⬅️ В главное меню":
        await back_to_main_menu(message, state)
        return
    if section not in qdata:
        await message.answer("Такого раздела нет. Выбери из списка.")
        return

    now = datetime.utcnow()
    uid = str(message.from_user.id)
    cooldowns = user_cooldowns.get(uid, {})
    last_time = cooldowns.get(section)
    if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
        mins = int((COOLDOWN_SECONDS - (now - last_time).total_seconds()) // 60) + 1
        await message.answer(f"⏱ Вы уже проходили этот раздел. Попробуйте снова через {mins} мин.")
        return

    questions = qdata[section]
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
            f"Ты можешь попробовать другие разделы или посмотреть свой результат в топе.",
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
    text = "<b>🏆 Топ игроков по правильным ответам:</b>\n\n"
    for i, (uid, bal) in enumerate(top, 1):
        user = await bot.get_chat(uid)
        name = user.full_name if user else f"User {uid}"
        text += f"{i}. <b>{name}</b> — {bal} баллов\n"
    await message.answer(text)

# === Пример команды для админа, чтобы добавить раздел прямо из чата ===
@dp.message(Command("addsection"))
async def add_section_cmd(message: types.Message):
    if message.from_user.id != 123456789:  # Укажи свой ID!
        await message.answer("Нет доступа.")
        return
    # Пример: /addsection [название]
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /addsection НазваниеРаздела")
        return
    section = args[1].strip()
    qdata = load_questions()
    if section in qdata:
        await message.answer("Такой раздел уже есть.")
        return
    qdata[section] = []
    save_questions(qdata)
    await message.answer(f"Раздел <b>{section}</b> добавлен!")

# === Инструкция для добавления новых вопросов ===

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "🛠 <b>Как добавить вопросы и разделы?</b>\n\n"
        "1. Открой файл <code>data/questions.json</code> на сервере или в редакторе.\n"
        "2. Добавь раздел, например:\n"
        "<code>{\n"
        "  \"Война за бизнес\": [\n"
        "    {\n"
        "      \"question\": \"Во сколько разрешено проводить войну за бизнес?\",\n"
        "      \"answers\": [\"С 00:00 до 12:00\", \"С 12:00 до 23:00\", \"С 18:00 до 06:00\", \"В любое время\"],\n"
        "      \"correct\": 1\n"
        "    }\n"
        "  ]\n"
        "}</code>\n"
        "3. Перезапусти бота, чтобы изменения вступили в силу.\n\n"
        "❗️ Или используй команду <code>/addsection НазваниеРаздела</code> (вопросы добавлять пока только через файл)."
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
