import asyncio
import os
print("Текущая рабочая директория:", os.getcwd())
print("Файлы в директории:", os.listdir())
import shutil
import json
import datetime
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
COOLDOWN_SECONDS = 5 * 60  # 5 минут на раздел
ADMIN_ID = 6712617550
PHOTO_FILE = "welcome_photo_id.json"
DATA_FILE = "data.json" 

def load_data():
    global user_scores, user_cooldowns, active_users
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                print("Содержимое data.json после сохранения:", f.read())
                data = json.load(f)
                user_scores = data.get("user_scores", {})
                # Преобразуем строки обратно в datetime
                user_cooldowns = {
                    uid: {sec: datetime.datetime.fromisoformat(dt) for sec, dt in cooldowns.items()}
                    for uid, cooldowns in data.get("user_cooldowns", {}).items()
                }
                active_users = set(data.get("active_users", []))
        except Exception as e:
            print("Ошибка чтения data.json:", e)
            # Попробуем восстановить из резервной копии
            backup = DATA_FILE + ".bak"
            if os.path.exists(backup):
                try:
                    with open(backup, "r") as f:
                        data = json.load(f)
                        user_scores = data.get("user_scores", {})
                        user_cooldowns = {
                            uid: {sec: datetime.datetime.fromisoformat(dt) for sec, dt in cooldowns.items()}
                            for uid, cooldowns in data.get("user_cooldowns", {}).items()
                        }
                        active_users = set(data.get("active_users", []))
                    print("Восстановлено из резервной копии!")
                    return
                except Exception as e2:
                    print("Ошибка чтения резервной копии:", e2)
            # Если не удалось — сбрасываем данные
            user_scores = {}
            user_cooldowns = {}
            active_users = set()
    else:
        user_scores = {}
        user_cooldowns = {}
        active_users = set()

def save_data():
    # сериализуем datetime в строки
    cooldowns_serializable = {
        uid: {sec: dt.isoformat() for sec, dt in cooldowns.items()}
        for uid, cooldowns in user_cooldowns.items()
    }
    data = {
        "user_scores": user_scores,
        "user_cooldowns": cooldowns_serializable,
        "active_users": list(active_users),
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            print("Содержимое data.json при загрузке:", f.read())
        shutil.copy(DATA_FILE, DATA_FILE + ".bak")
    tmp_file = DATA_FILE + ".tmp"
    with open(tmp_file, "w") as f:
        json.dump(data, f)
    os.replace(tmp_file, DATA_FILE)

SECTIONS = {
    "Война за бизнес": [
        {
            "question": "В какое время проводится война за бизнес?",
            "answers": [
                "С 09:00 до 20:00",
                "С 10:00 до 22:00",
                "С 12:00 до 23:00",
                "С 09:00 до 21:00"
            ],
            "correct": 2
        },
        {
            "question": "Сколько участников с каждой стороны может быть на территории бизнеса во время войны?",
            "answers": [
                "Больше 15",
                "От 5 до 15",
                "Хоть сколько",
                "Не больше 5"
            ],
            "correct": 1
        },
        {
            "question": "Сколько всего банд могут участвовать в одной войне за бизнес?",
            "answers": [
                "2",
                "3",
                "4",
                "5"
            ],
            "correct": 0
        },
        {
            "question": "Какое минимальное количество участников должно быть с каждой стороны для начала войны за бизнес?",
            "answers": [
                "2",
                "5",
                "6",
                "8"
            ],
            "correct": 1
        },
        {
            "question": "Можно ли использовать анимации /anim во время войны за бизнес?",
            "answers": [
                "Можно всегда",
                "Можно только в укрытии",
                "Нельзя",
                "Можно, если противник не видит"
            ],
            "correct": 2
        },
        {
            "question": "Можно ли использовать баги/недоработки сервера в войне за бизнес?",
            "answers": [
                "Да, если это помогает победить",
                "Нет, за это наказание",
                "Можно, если никто не заметит",
                "Только с разрешения администратора"
            ],
            "correct": 1
        },
        {
            "question": "Разрешено ли использовать транспорт для убийства участников во время войны?",
            "answers": [
                "Можно",
                "Можно только на территории",
                "Нельзя",
                "Можно, если противник согласен"
            ],
            "correct": 2
        },
        {
            "question": "Что происходит с участниками, которые зашли на территорию войны за бизнес без оружия?",
            "answers": [
                "Их могут убить, лидеру выдается выговор или бизвар не засчитывается",
                "Им выдается оружие и они играют бизвар",
                "Они удаляются с территории администрацией",
                "Ничего не происходит,такое разрешено"
            ],
            "correct": 0
        },
        {
            "question": "Можно ли использовать аптечки для восстановления здоровья во время войны за бизнес?",
            "answers": [
                "Можно в любое время",
                "Можно только за укрытием",
                "Нельзя",
                "Можно только вне территории"
            ],
            "correct": 1
        },
        {
            "question": "Что запрещено использовать для получения преимущества в войне за бизнес?",
            "answers": [
                "Читы, баги, сторонние программы",
                "Свою команду",
                "Прятаться за объектами",
                "Использование аптечек"
            ],
            "correct": 0
        },
        {
            "question": "Сколько времени дается на сбор участников после объявления войны?",
            "answers": [
                "20 минуты",
                "10 минуты",
                "30 минут",
                "15 минут"
            ],
            "correct": 2
        },
        {
            "question": "Когда можно объявить войну за бизнес?",
            "answers": [
                "В любое время",
                "Только после согласования с администрацией",
                "В строго установленные часы",
                "Только после выбора территории"
            ],
            "correct": 2
        },
        {
            "question": "Можно ли использовать маски во время войны за бизнес?",
            "answers": [
                "Можно",
                "Нельзя",
                "Можно только своим",
                "Можно только лидеру"
            ],
            "correct": 1
        },
        {
            "question": "Какая команда для назначения войны за бизнес в игре?",
            "answers": [
                "/biz",
                "/bizwar",
                "/bz",
                "/bwar"
            ],
            "correct": 1
        },
        {
            "question": "Сколько раз группировка может забить войну за бизнес в день? ",
            "answers": [
                "Хоть сколько",
                "Не более 3",
                "Только 4",
                "Не меньше 5"
            ],
            "correct": 2
        },
        {
            "question": "Сколько раз можно отказаться от участия в войне за бизнес?",
            "answers": [
                "Неограниченное количество",
                "Вообще нельзя",
                "1 раз",
                "2 раза"
            ],
            "correct": 3
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
        }, 
        {
            "question": "Какой должен быть формат Никнейма в игре",
            "answers": [
                "Фамилия_Имя",
                "Любого вида",
                "Фамилия_Имя_Отчество",
                "Имя_Фамилия"
            ],
            "correct": 3
        }
    ]
}

class QuizStates(StatesGroup):
    choosing_section = State()
    answering = State()
    waiting_broadcast = State()
    waiting_photo = State()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

user_cooldowns = {}
user_scores = {}
active_users = set()  # все, кто хотя бы раз проходил тест
load_data()

def main_menu(user_id=None):
    kb = [
        [types.KeyboardButton(text="🗂 Разделы вопросов")],
        [types.KeyboardButton(text="🏆 Топ 10 игроков")],
        [types.KeyboardButton(text="ℹ️ Помощь")]
    ]
    if user_id == ADMIN_ID:
        kb.append([types.KeyboardButton(text="👑 Админ-панель")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def sections_menu():
    kb = [[types.KeyboardButton(text=f"📚 {section}")] for section in SECTIONS.keys()]
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
        [types.KeyboardButton(text="🖼 Добавить фото к описанию")],
        [types.KeyboardButton(text="💾 Сохранить данные")],
        [types.KeyboardButton(text="📝 Показать данные")],
        [types.KeyboardButton(text="⬅️ В главное меню")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def load_photo_id():
    if os.path.exists(PHOTO_FILE):
        with open(PHOTO_FILE, "r") as f:
            data = json.load(f)
            return data.get("file_id")
    return None

def save_photo_id(file_id):
    with open(PHOTO_FILE, "w") as f:
        json.dump({"file_id": file_id}, f)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    photo_id = load_photo_id()
    caption = (
        "<b>🎮 Добро пожаловать в викторину Black Russia!</b>\n"
        "Выбирай раздел, отвечай на вопросы, зарабатывай баллы и попадай в топ!\n\n"
        "Нажми кнопку или /menu для начала."
    )
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
        save_data()
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
    if idx >= len(questions):
        # Завершаем раздел прямо здесь!
        uid = str(message.from_user.id)
        user_scores[uid] = user_scores.get(uid, 0) + score
        cooldowns = user_cooldowns.get(uid, {})
        cooldowns[section] = datetime.utcnow()
        user_cooldowns[uid] = cooldowns
        active_users.add(uid)
        save_data()
        await message.answer(
            f"✅ <b>Раздел \"{section}\" завершён!</b>\n"
            f"Твои баллы: <b>{score} из {len(questions)}</b>\n\n"
            f"Можешь попробовать другие разделы или посмотреть свой результат в топе.",
            reply_markup=main_menu(message.from_user.id)
        )
        await state.clear()
    else:
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

@dp.message(F.text == "👑 Админ-панель")
async def admin_panel(message: types.Message, state: FSMContext):
    print("DEBUG: message.from_user.id =", message.from_user.id)
    print("DEBUG: ADMIN_ID =", ADMIN_ID)
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

@dp.message(F.text == "🖼 Добавить фото к описанию")
async def add_photo_prompt(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await state.set_state(QuizStates.waiting_photo)
    await message.answer("Отправьте фото, которое будет использоваться в приветствии (/start).")

@dp.message(QuizStates.waiting_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    photo = message.photo[-1]
    save_photo_id(photo.file_id)
    await state.clear()
    await message.answer("Фото успешно сохранено! Теперь оно будет показываться в приветствии.", reply_markup=admin_menu())

@dp.message(QuizStates.waiting_photo)
async def handle_non_photo(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте именно фото.")

@dp.message(F.text == "💾 Сохранить данные")
async def save_data_admin(message: types.Message, state: FSMContext):
    print("НАЖАТА КНОПКА СОХРАНИТЬ ДАННЫЕ")  # <--- добавь это
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    save_data()
    await message.answer("Данные пользователей успешно сохранены!", reply_markup=admin_menu())
async def main():
    await dp.start_polling(bot)

@dp.message(F.text == "📝 Показать данные")
async def show_data_admin(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    import json
    await message.answer(f"<code>{json.dumps(user_scores, indent=2, ensure_ascii=False)}</code>")
    
if __name__ == "__main__":
    asyncio.run(main())
