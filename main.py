import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
ADMIN_IDS = {6712617550}  # Замени на свой user_id!
SUPPORT_USERNAME = "bunkoc"

CATEGORIES = {
    "Транспорт": [
        "Мото", "Авто", "Грузовой т/с", "Плавательные средства"
    ],
    "Аксессуары": [],
    "Одежда": [],
    "Недвижимость": [],
    "Бизнесы": [],
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

# --- Keyboards ---

def get_main_menu():
    kb = [
        [types.KeyboardButton(text="➕ Добавить объявление")],
        [types.KeyboardButton(text="📒 Каталог объявлений")],
        [types.KeyboardButton(text="💬 Поддержка")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_categories_kb():
    kb = [[types.KeyboardButton(text=cat)] for cat in CATEGORIES]
    kb.append([types.KeyboardButton(text="⬅️ Назад")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_subcategories_kb(category):
    kb = [[types.KeyboardButton(text=sub)] for sub in CATEGORIES[category]]
    kb.append([types.KeyboardButton(text="⬅️ Назад")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="⬅️ Назад")]],
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

def ads_paginate_kb(category, subcategory, page, total_pages):
    btns = []
    if page > 1:
        btns.append(types.InlineKeyboardButton("⏪ Назад", callback_data=f"page_{category}_{subcategory if subcategory else 'none'}_{page-1}"))
    if page < total_pages:
        btns.append(types.InlineKeyboardButton("Вперёд ⏩", callback_data=f"page_{category}_{subcategory if subcategory else 'none'}_{page+1}"))
    if btns:
        return types.InlineKeyboardMarkup(inline_keyboard=[btns])
    return None

# --- Старт и главное меню ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>👋 Добро пожаловать в каталог объявлений Black Russia! для сервера KOSTROMA #77</b>\n\n"
        "Здесь вы можете удобно размещать и искать объявления по категориям.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "💬 Поддержка")
async def support(message: types.Message):
    await message.answer(
        "<b>Техническая поддержка</b>\n\n"
        "Если возникли вопросы или проблемы, обратитесь к администратору:\n"
        f"👉 <a href='https://t.me/{SUPPORT_USERNAME}'>@{SUPPORT_USERNAME}</a>",
        disable_web_page_preview=True,
        reply_markup=get_main_menu()
    )

# --- Добавление объявления ---

@dp.message(F.text == "➕ Добавить объявление")
async def add_ad_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>Добавление объявления</b>\n\n"
        "Выберите категорию:",
        reply_markup=get_categories_kb()
    )
    await state.set_state(AddAd.category)

@dp.message(AddAd.category)
async def add_ad_category(message: types.Message, state: FSMContext):
    cat = message.text
    if cat == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_menu())
        return
    if cat not in CATEGORIES:
        await message.answer("Пожалуйста, выберите категорию из списка.", reply_markup=get_categories_kb())
        return
    await state.update_data(category=cat)
    if CATEGORIES[cat]:
        await message.answer(
            "<b>Подкатегория</b>\n\nВыберите подкатегорию:",
            reply_markup=get_subcategories_kb(cat)
        )
        await state.set_state(AddAd.subcategory)
    else:
        await state.update_data(subcategory="")
        await message.answer("Введите название объявления:", reply_markup=get_cancel_kb())
        await state.set_state(AddAd.title)

@dp.message(AddAd.subcategory)
async def add_ad_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    sub = message.text
    if sub == "⬅️ Назад":
        await message.answer("Выберите категорию:", reply_markup=get_categories_kb())
        await state.set_state(AddAd.category)
        return
    if sub not in CATEGORIES[cat]:
        await message.answer("Пожалуйста, выберите подкатегорию из списка.", reply_markup=get_subcategories_kb(cat))
        return
    await state.update_data(subcategory=sub)
    await message.answer("Введите название объявления:", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.title)

@dp.message(AddAd.title)
async def add_ad_title(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        cat = data["category"]
        if cat and CATEGORIES[cat]:
            await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_kb(cat))
            await state.set_state(AddAd.subcategory)
        else:
            await message.answer("Выберите категорию:", reply_markup=get_categories_kb())
            await state.set_state(AddAd.category)
        return
    await state.update_data(title=message.text)
    await message.answer("Введите описание объявления:", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.description)

@dp.message(AddAd.description)
async def add_ad_description(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Введите название объявления:", reply_markup=get_cancel_kb())
        await state.set_state(AddAd.title)
        return
    await state.update_data(description=message.text)
    await message.answer("Введите контакты для связи (телефон, Telegram и т.д.):", reply_markup=get_cancel_kb())
    await state.set_state(AddAd.contacts)

@dp.message(AddAd.contacts)
async def add_ad_contacts(message: types.Message, state: FSMContext):
    global ad_id_counter
    if message.text == "⬅️ Назад":
        await message.answer("Введите описание объявления:", reply_markup=get_cancel_kb())
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
        "<b>✅ Объявление добавлено!</b>\n\n"
        "Спасибо, ваше объявление сохранено и доступно в каталоге.",
        reply_markup=get_main_menu()
    )

# --- Просмотр объявлений с пагинацией ---

@dp.message(F.text == "📒 Каталог объявлений")
async def show_categories(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите категорию для просмотра:", reply_markup=get_categories_kb())

@dp.message(F.text.in_(CATEGORIES.keys()))
async def show_subcategories(message: types.Message, state: FSMContext):
    cat = message.text
    if cat == "⬅️ Назад":
        await message.answer("Главное меню:", reply_markup=get_main_menu())
        return
    await state.update_data(selected_category=cat)
    if CATEGORIES[cat]:
        await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_kb(cat))
    else:
        await send_ads(message, category=cat, subcategory=None, page=1, show_back=True)

@dp.message()
async def show_ads_by_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data.get("selected_category")
    if not cat:
        return
    sub = message.text
    if sub == "⬅️ Назад":
        await message.answer("Выберите категорию:", reply_markup=get_categories_kb())
        return
    if sub not in CATEGORIES[cat]:
        return
    await send_ads(message, category=cat, subcategory=sub, page=1, show_back=True)

async def send_ads(message, category, subcategory, page=1, show_back=False):
    filtered = [
        ad for ad in ADS
        if ad["category"] == category and (subcategory is None or ad["subcategory"] == subcategory)
    ]
    if not filtered:
        back = "⬅️ Назад" if show_back else None
        await message.answer(
            "<b>Объявлений не найдено.</b>",
            reply_markup=get_cancel_kb() if back else None
        )
        return

    page_size = 5
    total_pages = (len(filtered) + page_size - 1) // page_size
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    for ad in items:
        text = (
            f"<b>{ad['title']}</b>\n"
            f"<b>Категория:</b> {ad['category']}" +
            (f" / {ad['subcategory']}" if ad['subcategory'] else "") +
            f"\n{ad['description']}\n"
            f"<i>Контакты:</i> {ad['contacts']}\n"
            f"<i>Автор:</i> {ad['user_name']}"
        )
        kb = get_ad_kb(ad, message.from_user.id)
        await message.answer(text, reply_markup=kb)

    pag_kb = ads_paginate_kb(category, subcategory, page, total_pages)
    back_kb = None
    if show_back:
        back_kb = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        )
    if pag_kb:
        await message.answer(
            f"Страница <b>{page} из {total_pages}</b>",
            reply_markup=pag_kb
        )
    elif back_kb:
        await message.answer("Для возврата используйте кнопку ниже.", reply_markup=back_kb)

@dp.callback_query(F.data.startswith("page_"))
async def paginate_ads(call: types.CallbackQuery, state: FSMContext):
    _, cat, sub, page = call.data.split("_", 3)
    if sub == "none":
        sub = None
    else:
        await state.update_data(selected_category=cat)
    await call.answer()
    await send_ads(call.message, category=cat, subcategory=sub, page=int(page), show_back=True)

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
    await call.message.answer("Введите новое <b>название</b> объявления:", reply_markup=get_cancel_kb())
    await state.set_state(EditAd.editing_title)

@dp.callback_query(EditAd.choosing_field, F.data == "edit_field_description")
async def edit_description(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Введите новое <b>описание</b> объявления:", reply_markup=get_cancel_kb())
    await state.set_state(EditAd.editing_description)

@dp.callback_query(EditAd.choosing_field, F.data == "edit_field_contacts")
async def edit_contacts(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Введите новые <b>контакты</b>:", reply_markup=get_cancel_kb())
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
