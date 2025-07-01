import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime

BOT_TOKEN = "ВАШ_ТОКЕН_ТУТ"
COOLDOWN_SECONDS = 5 * 60  # 5 минут на раздел
ADMIN_ID = 6712617550

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

class QuizStates(StatesGroup):
    choosing_section = State()
    answering = State()
    waiting_broadcast = State()

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

user_cooldowns = {}
user_scores = {}
active_users = set()  # все, кто хотя бы раз проходил тест

def main_menu(user_id=None):
    kb = [
        [types.KeyboardButton(text="🗂 Разделы вопросов")],
        [types.KeyboardButton(text="🏆 Топ 10 игроков")],
        [types.KeyboardButton(text="ℹ️ Помощь")]
    ]
    # Только для админа - кнопка админ-панели
    if user_id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="👑 Админ-панель")])
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

def support_menu():
    url = "https://t.me/bunkoc"
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🧑‍💻 Написать в поддержку", url=url)]
        ]
    )

def admin_menu():
    kb = [
        [types.KeyboardButton(text="📢 Оповестить пользователей")],
        [types.KeyboardButton(text="⬅️ В главное меню")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>🎮 Добро пожаловать в викторину Black Russia!</b>\n"
        "Выбирай раздел, отвечай на вопросы, зарабатывай баллы и попадай в топ!\n\n"
        "Нажми кнопку или /menu для начала.",
        reply_markup=main_menu(message.from_user.id)
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 <b>Главное меню:</b>", reply_markup=main_menu(message.from_user.id))

@dp.message(F.text == "⬅️ В главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await cmd_menu(message, state)

@dp.message(F.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    text = (
        "<b>🕹 О боте и системе баллов</b>\n\n"
        "Это викторина по тематике Black Russia!\n"
        "Выбирай интересующий раздел и отвечай на вопросы.\n"
        "За каждый правильный ответ ты получаешь 1 балл.\n"
        "<b>Каждый раздел можно проходить только 1 раз в 5 минут.</b>\n"
        "Ограничение действует отдельно для каждого раздела.\n"
        "Разделы вопросов будут дополняться ежедневно.\n\n"
        "Следи за обновлениями и попадай в топ игроков!\n\n"
        "Поддержка — <b>@bunkoc</b> (жми кнопку ниже для личных сообщений).\n"
        "Удачи!"
    )
    await message.answer(text, reply_markup=support_menu())

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
        active_users.add(uid)
        await message.answer(
            f"✅ <b>Раздел \"{section}\" завершён!</b>\n"
            f"Твои баллы: <b>{data['score']} из {len(questions)}</b>\n\n"
            f"Можешь попробовать другие разделы или посмотреть свой результат в топе.",
            reply_markup=main_menu(message.from_user.id)
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
            username = f"@{user.username}" if user and user.username else ""
        except Exception:
            name = f"User {uid}"
            username = ""
        text += f"{i}. <b>{name}</b> {f'({username})' if username else ''} — {bal} баллов\n"
    await message.answer(text)

# ==== Админ-панель ====
@dp.message(F.text == "👑 Админ-панель")
async def admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await state.clear()
    await message.answer("👑 <b>Админ-панель</b>\n\nВыберите действие:", reply_markup=admin_menu())

@dp.message(F.text == "📢 Оповестить пользователей")
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await state.set_state(QuizStates.waiting_broadcast)
    await message.answer("Введите текст рассылки для всех пользователей. Для отмены — /menu")

@dp.message(QuizStates.waiting_broadcast)
async def broadcast_message(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    text = message.text
    if not text or text.startswith("/"):
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=main_menu(ADMIN_ID))
        return
    await message.answer("Рассылка началась, ожидайте завершения...", reply_markup=main_menu(ADMIN_ID))
    count = 0
    for uid in active_users:
        try:
            await bot.send_message(uid, f"📢 <b>Оповещение от админа:</b>\n\n{text}")
            count += 1
        except Exception:
            pass
    await state.clear()
    await message.answer(f"Рассылка завершена. Получателей: {count}", reply_markup=admin_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
