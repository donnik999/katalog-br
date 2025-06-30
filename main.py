import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_IDS = {6712617550}
SUPPORT_USERNAME = "bunkoc"

CATEGORIES = {
    "🚗 Транспорт": [
        "🏍 Мото", "🚙 Авто", "🚚 Грузовой т/с", "🛥 Плавательные средства"
    ],
    "🎩 Аксессуары": [],
    "👕 Одежда": [],
    "🏠 Недвижимость": [],
    "🏪 Бизнесы": [],
}

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

ADS = []
ad_id_counter = 1

class AddAd(StatesGroup):
    category = State()
    subcategory = State()
    title = State()
    description = State()
    contacts = State()

class EditAd(StatesGroup):
    choosing_field = State()
    editing_title = State()
    editing_description = State()
    editing_contacts = State()

# --- Клавиатуры ---

def get_main_menu():
    kb = [
        [types.KeyboardButton(text="➕ Добавить объявление")],
        [types.KeyboardButton(text="📒 Каталог объявлений")],
        [types.KeyboardButton(text="💬 Поддержка")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_categories_kb():
    kb = [[types.KeyboardButton(text=cat)] for cat in CATEGORIES]
    kb.append([types.KeyboardButton(text="⬅️ В главное меню")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_subcategories_kb(category):
    kb = [[types.KeyboardButton(text=sub)] for sub in CATEGORIES[category]]
    kb.append([types.KeyboardButton(text="⬅️ Назад к категориям")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_kb(text="⬅️ Назад"):
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=text)]],
        resize_keyboard=True
    )

def get_ad_kb(ad, user_id):
    kb = []
    row = []
    if ad["user_id"] == user_id or user_id in ADMIN_IDS:
        row.append(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{ad['id']}"))
    if ad["user_id"] == user_id:
        row.append(types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{ad['id']}"))
    if row:
        kb.append(row)
    return types.InlineKeyboardMarkup(inline_keyboard=kb) if kb else None

# --- Старт и главное меню ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>👋 Добро пожаловать в <u>Black Russia Market</u>!</b>\n\n"
        "Здесь вы можете удобно размещать и искать объявления по категориям.\n\n"
        "<b>Выберите действие:</b>",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "⬅️ В главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 <b>Главное меню:</b>", reply_markup=get_main_menu())

@dp.message(F.text == "💬 Поддержка")
async def support(message: types.Message):
    await message.answer(
        "<b>💬 Техническая поддержка</b>\n\n"
        "Если возникли вопросы или проблемы — обращайтесь:\n"
        f"👉 <a href='https://t.me/{SUPPORT_USERNAME}'>@{SUPPORT_USERNAME}</a>",
        disable_web_page_preview=True,
        reply_markup=get_main_menu()
    )

# --- Добавление объявления ---

@dp.message(F.text == "➕ Добавить объявление")
async def add_ad_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>📝 Добавление объявления</b>\n\n"
        "🔻 <b>Выберите категорию:</b>",
        reply_markup=get_categories_kb()
    )
    await state.set_state(AddAd.category)

@dp.message(AddAd.category)
async def add_ad_category(message: types.Message, state: FSMContext):
    cat = message.text
    if cat == "⬅️ В главное меню":
        await state.clear()
        await message.answer("🔝 <b>Главное меню:</b>", reply_markup=get_main_menu())
        return
    if cat not in CATEGORIES:
        await message.answer("❗️ Пожалуйста, выберите категорию из списка.", reply_markup=get_categories_kb())
        return
    await state.update_data(category=cat)
    if CATEGORIES[cat]:
        await message.answer(
            f"<b>{cat}</b>\n\n🔻 <b>Выберите подкатегорию:</b>",
            reply_markup=get_subcategories_kb(cat)
        )
        await state.set_state(AddAd.subcategory)
    else:
        await state.update_data(subcategory="")
        await message.answer("✏️ <b>Введите название объявления:</b>", reply_markup=get_cancel_kb())
        await state.set_state(AddAd.title)

@dp.message(AddAd.subcategory)
async def add_ad_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    sub = message.text
    if sub == "⬅️ Назад к категориям":
        await message.answer("🔻 <b>Выберите категорию:</b>", reply_markup=get_categories_kb())
        await state.set_state(AddAd.category)
        return
    if sub not in CATEGORIES[cat]:
        await message.answer("❗️ Пожалуйста, выберите подкатегорию из списка.", reply_markup=get_subcategories_kb(cat))
        return
    await state.update_data(subcategory=sub)
    await message.answer("✏️ <b>Введите название объявления:</b>", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.title)

@dp.message(AddAd.title)
async def add_ad_title(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        cat = data["category"]
        if cat and CATEGORIES[cat]:
            await message.answer("🔻 <b>Выберите подкатегорию:</b>", reply_markup=get_subcategories_kb(cat))
            await state.set_state(AddAd.subcategory)
        else:
            await message.answer("🔻 <b>Выберите категорию:</b>", reply_markup=get_categories_kb())
            await state.set_state(AddAd.category)
        return
    await state.update_data(title=message.text)
    await message.answer("📝 <b>Введите описание объявления:</b>", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.description)

@dp.message(AddAd.description)
async def add_ad_description(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("✏️ <b>Введите название объявления:</b>", reply_markup=get_cancel_kb())
        await state.set_state(AddAd.title)
        return
    await state.update_data(description=message.text)
    await message.answer("📱 <b>Введите контакты для связи (Telegram, телефон и т.д.):</b>", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.contacts)

@dp.message(AddAd.contacts)
async def add_ad_contacts(message: types.Message, state: FSMContext):
    global ad_id_counter
    if message.text == "⬅️ Назад":
        await message.answer("📝 <b>Введите описание объявления:</b>", reply_markup=get_cancel_kb())
        await state.set_state(AddAd.description)
        return
    data = await state.get_data()
    ad = {
        "id": ad_id_counter,
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "category": data["category"],
        "subcategory": data.get("subcategory", ""),
        "title": data["title"],
        "description": data["description"],
        "contacts": message.text
    }
    ADS.append(ad)
    ad_id_counter += 1
    await state.clear()
    await message.answer(
        "<b>✅ Ваше объявление добавлено!</b>\n\n"
        "Оно теперь доступно в каталоге.",
        reply_markup=get_main_menu()
    )

# --- Просмотр объявлений ---

@dp.message(F.text == "📒 Каталог объявлений")
async def show_categories(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔻 <b>Выберите категорию для просмотра:</b>", reply_markup=get_categories_kb())
    await state.set_data({"nav_level": "categories"})

@dp.message(F.text.in_(CATEGORIES.keys()))
async def show_subcategories(message: types.Message, state: FSMContext):
    cat = message.text
    if cat == "⬅️ В главное меню":
        await state.clear()
        await message.answer("🔝 <b>Главное меню:</b>", reply_markup=get_main_menu())
        return
    await state.update_data(selected_category=cat, nav_level="subcategories")
    if CATEGORIES[cat]:
        await message.answer("🔻 <b>Выберите подкатегорию:</b>", reply_markup=get_subcategories_kb(cat))
    else:
        await send_all_ads(message, category=cat, subcategory=None, show_back=True)
        await state.update_data(nav_level="ads")

@dp.message()
async def show_ads_by_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nav_level = data.get("nav_level")
    cat = data.get("selected_category")
    if not cat or nav_level not in ("subcategories", "ads"):
        return
    sub = message.text
    if sub == "⬅️ Назад к категориям":
        await show_categories(message, state)
        return
    if sub == "⬅️ Назад":
        if nav_level == "subcategories":
            await show_categories(message, state)
        elif nav_level == "ads":
            if CATEGORIES[cat]:
                await message.answer("🔻 <b>Выберите подкатегорию:</b>", reply_markup=get_subcategories_kb(cat))
                await state.update_data(nav_level="subcategories")
            else:
                await show_categories(message, state)
        return
    if sub not in CATEGORIES[cat]:
        return
    await send_all_ads(message, category=cat, subcategory=sub, show_back=True)
    await state.update_data(nav_level="ads")

async def send_all_ads(message, category, subcategory, show_back=False):
    filtered = [
        ad for ad in ADS
        if ad["category"] == category and (subcategory is None or ad["subcategory"] == subcategory)
    ]
    if not filtered:
        back = "⬅️ Назад" if show_back else None
        await message.answer(
            "<b>🔎 Объявлений не найдено.</b>",
            reply_markup=get_cancel_kb() if back else None
        )
        return
    for ad in filtered:
        text = (
            f"🔹 <b>{ad['title']}</b>\n"
            f"<b>Категория:</b> {ad['category']}" +
            (f" / {ad['subcategory']}" if ad['subcategory'] else "") +
            f"\n\n{ad['description']}\n"
            f"📱 <b>Контакты:</b> <code>{ad['contacts']}</code>\n"
            f"👤 <i>Автор:</i> {ad['user_name']}"
        )
        kb = get_ad_kb(ad, message.from_user.id)
        await message.answer(text, reply_markup=kb)
    if show_back:
        back_kb = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        )
        await message.answer("Для возврата используйте кнопку ниже.", reply_markup=back_kb)

# --- Удаление и редактирование объявлений ---

@dp.callback_query(F.data.startswith("delete_"))
async def delete_ad(call: types.CallbackQuery):
    ad_id = int(call.data.split("_")[1])
    global ADS
    ad = next((ad for ad in ADS if ad["id"] == ad_id), None)
    if ad and (call.from_user.id == ad["user_id"] or call.from_user.id in ADMIN_IDS):
        ADS = [a for a in ADS if a["id"] != ad_id]
        await call.answer("Удалено.")
        await call.message.delete()
    else:
        await call.answer("Недостаточно прав для удаления", show_alert=True)

@dp.callback_query(F.data.startswith("edit_"))
async def edit_ad_start(call: types.CallbackQuery, state: FSMContext):
    ad_id = int(call.data.split("_")[1])
    ad = next((ad for ad in ADS if ad["id"] == ad_id), None)
    if not ad or call.from_user.id != ad["user_id"]:
        await call.answer("Недостаточно прав для редактирования", show_alert=True)
        return
    await state.update_data(edit_ad_id=ad_id)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton("Название", callback_data="edit_field_title"),
                types.InlineKeyboardButton("Описание", callback_data="edit_field_description"),
                types.InlineKeyboardButton("Контакты", callback_data="edit_field_contacts")
            ],
            [types.InlineKeyboardButton("Отмена", callback_data="edit_cancel")]
        ]
    )
    await call.answer()
    await call.message.answer("<b>Что хотите изменить?</b>", reply_markup=kb)
    await state.set_state(EditAd.choosing_field)

@dp.callback_query(EditAd.choosing_field, F.data == "edit_cancel")
async def edit_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("Редактирование отменено.", show_alert=True)
    await call.message.delete()

@dp.callback_query(EditAd.choosing_field, F.data == "edit_field_title")
async def edit_title(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("✏️ <b>Введите новое название:</b>", reply_markup=get_cancel_kb())
    await state.set_state(EditAd.editing_title)

@dp.callback_query(EditAd.choosing_field, F.data == "edit_field_description")
async def edit_description(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📝 <b>Введите новое описание:</b>", reply_markup=get_cancel_kb())
    await state.set_state(EditAd.editing_description)

@dp.callback_query(EditAd.choosing_field, F.data == "edit_field_contacts")
async def edit_contacts(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📱 <b>Введите новые контакты:</b>", reply_markup=get_cancel_kb())
    await state.set_state(EditAd.editing_contacts)

@dp.message(EditAd.editing_title)
async def edit_title_input(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(EditAd.choosing_field)
        await message.answer("<b>Что хотите изменить?</b>")
        return
    data = await state.get_data()
    ad_id = data["edit_ad_id"]
    for ad in ADS:
        if ad["id"] == ad_id and ad["user_id"] == message.from_user.id:
            ad["title"] = message.text
            await message.answer("<b>Название изменено!</b>", reply_markup=get_main_menu())
            await state.clear()
            return

@dp.message(EditAd.editing_description)
async def edit_description_input(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(EditAd.choosing_field)
        await message.answer("<b>Что хотите изменить?</b>")
        return
    data = await state.get_data()
    ad_id = data["edit_ad_id"]
    for ad in ADS:
        if ad["id"] == ad_id and ad["user_id"] == message.from_user.id:
            ad["description"] = message.text
            await message.answer("<b>Описание изменено!</b>", reply_markup=get_main_menu())
            await state.clear()
            return

@dp.message(EditAd.editing_contacts)
async def edit_contacts_input(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(EditAd.choosing_field)
        await message.answer("<b>Что хотите изменить?</b>")
        return
    data = await state.get_data()
    ad_id = data["edit_ad_id"]
    for ad in ADS:
        if ad["id"] == ad_id and ad["user_id"] == message.from_user.id:
            ad["contacts"] = message.text
            await message.answer("<b>Контакты изменены!</b>", reply_markup=get_main_menu())
            await state.clear()
            return

# --- Запуск ---

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
