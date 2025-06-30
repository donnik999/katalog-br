import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Вставь сюда свой токен!
BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"
# Замени на свой Telegram user_id (можно узнать у @userinfobot)
ADMIN_IDS = {6712617550}

CATEGORIES = {
    "Транспорт": [
        "Мото", "Авто", "Грузовой т/с", "Плавательные средства"
    ],
    "Аксессуары": [],
    "Одежда": [],
    "Недвижимость": [],
    "Бизнесы": [],
}

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
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

def get_main_menu():
    kb = [
        [types.KeyboardButton(text="➕ Добавить объявление")],
        [types.KeyboardButton(text="📒 Каталог объявлений")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_categories_kb():
    kb = [[types.KeyboardButton(text=cat)] for cat in CATEGORIES]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_subcategories_kb(category):
    kb = [[types.KeyboardButton(text=sub)] for sub in CATEGORIES[category]]
    kb.append([types.KeyboardButton(text="Назад")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_ad_kb(ad, user_id):
    kb = []
    if ad["user_id"] == user_id or user_id in ADMIN_IDS:
        kb.append([types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{ad['id']}")])
    return types.InlineKeyboardMarkup(inline_keyboard=kb) if kb else None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Добро пожаловать в каталог объявлений Black Russia!</b>\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
    )

@dp.message(F.text == "➕ Добавить объявление")
async def add_ad_start(message: types.Message, state: FSMContext):
    await message.answer("Выберите категорию:", reply_markup=get_categories_kb())
    await state.set_state(AddAd.category)

@dp.message(AddAd.category)
async def add_ad_category(message: types.Message, state: FSMContext):
    cat = message.text
    if cat not in CATEGORIES:
        await message.answer("Пожалуйста, выберите категорию из списка.")
        return
    await state.update_data(category=cat)
    if CATEGORIES[cat]:
        await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_kb(cat))
        await state.set_state(AddAd.subcategory)
    else:
        await state.update_data(subcategory="")
        await message.answer("Введите название объявления:")
        await state.set_state(AddAd.title)

@dp.message(AddAd.subcategory)
async def add_ad_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    sub = message.text
    if sub == "Назад":
        await message.answer("Выберите категорию:", reply_markup=get_categories_kb())
        await state.set_state(AddAd.category)
        return
    if sub not in CATEGORIES[cat]:
        await message.answer("Пожалуйста, выберите подкатегорию из списка.")
        return
    await state.update_data(subcategory=sub)
    await message.answer("Введите название объявления:")
    await state.set_state(AddAd.title)

@dp.message(AddAd.title)
async def add_ad_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание объявления:")
    await state.set_state(AddAd.description)

@dp.message(AddAd.description)
async def add_ad_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите контакты для связи (телефон, Telegram и т.д.):")
    await state.set_state(AddAd.contacts)

@dp.message(AddAd.contacts)
async def add_ad_contacts(message: types.Message, state: FSMContext):
    global ad_id_counter
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
    await message.answer("✅ Объявление добавлено!", reply_markup=get_main_menu())
    await state.clear()

@dp.message(F.text == "📒 Каталог объявлений")
async def show_categories(message: types.Message):
    await message.answer("Выберите категорию для просмотра:", reply_markup=get_categories_kb())

@dp.message(F.text.in_(CATEGORIES.keys()))
async def show_subcategories(message: types.Message, state: FSMContext):
    cat = message.text
    await state.update_data(selected_category=cat)
    if CATEGORIES[cat]:
        await message.answer("Выберите подкатегорию:", reply_markup=get_subcategories_kb(cat))
    else:
        await send_ads(message, category=cat, subcategory=None)

@dp.message(F.text.in_(sum(CATEGORIES.values(), [])))
async def show_ads_by_subcategory(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data.get("selected_category")
    if not cat:
        await message.answer("Сначала выберите категорию.")
        return
    sub = message.text
    await send_ads(message, category=cat, subcategory=sub)

async def send_ads(message, category, subcategory):
    found = []
    for ad in ADS:
        if ad["category"] == category and (not subcategory or ad["subcategory"] == subcategory):
            found.append(ad)
    if not found:
        await message.answer("Объявлений не найдено.")
        return
    for ad in found:
        text = (
            f"<b>{ad['title']}</b>\n"
            f"<b>Категория:</b> {ad['category']}"
            + (f" / {ad['subcategory']}" if ad['subcategory'] else "") + "\n"
            f"{ad['description']}\n"
            f"<i>Контакты:</i> {ad['contacts']}\n"
            f"<i>Автор:</i> {ad['user_name']}"
        )
        kb = get_ad_kb(ad, message.from_user.id)
        await message.answer(text, reply_markup=kb)

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
