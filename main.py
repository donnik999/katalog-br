import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import asyncio
import os

# ВСТАВЬТЕ СВОЙ ТОКЕН ТУТ
BOT_TOKEN = "7220830808:AAE7R_edzGpvUNboGOthydsT9m81TIfiqzU"

# Ваш Telegram ID для админских действий (укажите свой ID)
ADMIN_IDS = [6712617550]  # замените на свой id

# Логирование
logging.basicConfig(level=logging.INFO)

# FSM состояния
class AdCreation(StatesGroup):
    category = State()
    subcategory = State()
    title = State()
    description = State()
    price = State()
    confirm = State()

# Память для объявлений (замените на базу данных при необходимости)
ads = []
ad_id_counter = 1

# Категории и подкатегории
CATEGORIES = {
    "Транспорт": {
        "Мото": "Мото",
        "Авто": "Авто",
        "Грузовой т/с": "Грузовой т/с",
        "Плавательные средства": "Плавательные средства",
    },
    "Аксессуары": None,
    "Одежда": None,
    "Недвижимость": None,
    "Бизнесы": None
}

def get_main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Разместить объявление", callback_data="add_ad")
    kb.button(text="🗂 Каталог объявлений", callback_data="catalog")
    kb.button(text="ℹ️ О боте", callback_data="about")
    kb.adjust(1)
    return kb.as_markup()

def get_categories_menu():
    kb = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        kb.button(text=cat, callback_data=f"cat_{cat}")
    kb.button(text="🔙 Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()

def get_subcategories_menu(category):
    kb = InlineKeyboardBuilder()
    for subcat in CATEGORIES[category]:
        kb.button(text=subcat, callback_data=f"subcat_{subcat}")
    kb.button(text="🔙 Назад", callback_data="choose_category")
    kb.adjust(1)
    return kb.as_markup()

def get_catalog_menu():
    kb = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        kb.button(text=cat, callback_data=f"catalog_{cat}")
    kb.button(text="🔙 Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()

def get_ads_by_category(cat, subcat=None):
    filtered = []
    for ad in ads:
        if ad['category'] == cat:
            if subcat:
                if ad.get('subcategory') == subcat:
                    filtered.append(ad)
            else:
                filtered.append(ad)
    return filtered

def get_my_ads(user_id):
    return [ad for ad in ads if ad['user_id'] == user_id]

def get_ad_menu(ad, user_id):
    kb = InlineKeyboardBuilder()
    if user_id in ADMIN_IDS or ad["user_id"] == user_id:
        kb.button(text="🗑 Удалить", callback_data=f"delete_{ad['id']}")
    kb.button(text="🔙 Назад", callback_data="catalog")
    kb.adjust(1)
    return kb.as_markup()

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def start(message: Message):
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\nДобро пожаловать в бот объявлений по Black Russia.",
            reply_markup=get_main_menu()
        )

    @dp.message(Command("menu"))
    async def menu(message: Message):
        await message.answer("Главное меню:", reply_markup=get_main_menu())

    @dp.callback_query(F.data == "main_menu")
    async def cb_main_menu(callback: CallbackQuery):
        await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())

    @dp.callback_query(F.data == "about")
    async def cb_about(callback: CallbackQuery):
        await callback.message.edit_text(
            "🤖 Этот бот предназначен для размещения и просмотра объявлений по игре Black Russia (CRMP Mobile).\n\n"
            "Вы можете размещать свои объявления, просматривать каталог и связываться с продавцами.",
            reply_markup=get_main_menu()
        )

    # Добавить объявление
    @dp.callback_query(F.data == "add_ad")
    async def cb_add_ad(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await state.set_state(AdCreation.category)
        kb = get_categories_menu()
        await callback.message.edit_text("Выберите категорию:", reply_markup=kb)

    @dp.callback_query(F.data.startswith("cat_"))
    async def cb_choose_subcat(callback: CallbackQuery, state: FSMContext):
        category = callback.data[4:]
        await state.update_data(category=category)
        if CATEGORIES[category]:
            kb = get_subcategories_menu(category)
            await state.set_state(AdCreation.subcategory)
            await callback.message.edit_text("Выберите подкатегорию:", reply_markup=kb)
        else:
            await state.set_state(AdCreation.title)
            await callback.message.edit_text("Введите заголовок объявления:")

    @dp.callback_query(F.data.startswith("subcat_"))
    async def cb_subcat(callback: CallbackQuery, state: FSMContext):
        subcategory = callback.data[7:]
        await state.update_data(subcategory=subcategory)
        await state.set_state(AdCreation.title)
        await callback.message.edit_text("Введите заголовок объявления:")

    @dp.message(AdCreation.category)
    async def msg_category(message: Message, state: FSMContext):
        await message.answer("Пожалуйста, выберите категорию через меню выше.")

    @dp.message(AdCreation.subcategory)
    async def msg_subcategory(message: Message, state: FSMContext):
        await message.answer("Пожалуйста, выберите подкатегорию через меню выше.")

    @dp.message(AdCreation.title)
    async def msg_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text)
        await state.set_state(AdCreation.description)
        await message.answer("Введите описание объявления:")

    @dp.message(AdCreation.description)
    async def msg_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        await state.set_state(AdCreation.price)
        await message.answer("Укажите цену:")

    @dp.message(AdCreation.price)
    async def msg_price(message: Message, state: FSMContext):
        await state.update_data(price=message.text)
        data = await state.get_data()
        text = "<b>Проверьте объявление:</b>\n\n"
        text += f"<b>Категория:</b> {data.get('category')}\n"
        if data.get('subcategory'):
            text += f"<b>Подкатегория:</b> {data.get('subcategory')}\n"
        text += f"<b>Заголовок:</b> {data.get('title')}\n"
        text += f"<b>Описание:</b> {data.get('description')}\n"
        text += f"<b>Цена:</b> {data.get('price')}\n"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm_ad"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_ad")
                ]
            ]
        )
        await state.set_state(AdCreation.confirm)
        await message.answer(text, reply_markup=kb)

    @dp.callback_query(F.data == "cancel_ad")
    async def cb_cancel_ad(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text("Создание объявления отменено.", reply_markup=get_main_menu())

    @dp.callback_query(F.data == "confirm_ad")
    async def cb_confirm_ad(callback: CallbackQuery, state: FSMContext):
        global ad_id_counter
        data = await state.get_data()
        ad = {
            "id": ad_id_counter,
            "user_id": callback.from_user.id,
            "username": callback.from_user.username,
            "category": data.get("category"),
            "subcategory": data.get("subcategory"),
            "title": data.get("title"),
            "description": data.get("description"),
            "price": data.get("price"),
        }
        ads.append(ad)
        ad_id_counter += 1
        await state.clear()
        await callback.message.edit_text("✅ Объявление успешно опубликовано!", reply_markup=get_main_menu())

    # Каталог
    @dp.callback_query(F.data == "catalog")
    async def cb_catalog(callback: CallbackQuery):
        await callback.message.edit_text("Выберите категорию:", reply_markup=get_catalog_menu())

    @dp.callback_query(F.data.startswith("catalog_"))
    async def cb_catalog_category(callback: CallbackQuery):
        cat = callback.data[8:]
        if CATEGORIES[cat]:
            kb = InlineKeyboardBuilder()
            for subcat in CATEGORIES[cat]:
                kb.button(text=subcat, callback_data=f"catalog_{cat}_{subcat}")
            kb.button(text="🔙 Назад", callback_data="catalog")
            kb.adjust(1)
            await callback.message.edit_text(f"Выберите подкатегорию для {cat}:", reply_markup=kb.as_markup())
        else:
            matched_ads = get_ads_by_category(cat)
            if not matched_ads:
                await callback.message.edit_text("Объявлений не найдено.", reply_markup=get_catalog_menu())
                return
            await send_ads_list(callback, matched_ads, cat)

    @dp.callback_query(F.data.regexp(r"^catalog_(.+)_(.+)$"))
    async def cb_catalog_subcat(callback: CallbackQuery):
        _, cat, subcat = callback.data.split("_", 2)
        matched_ads = get_ads_by_category(cat, subcat)
        if not matched_ads:
            await callback.message.edit_text("Объявлений не найдено.", reply_markup=get_catalog_menu())
            return
        await send_ads_list(callback, matched_ads, cat, subcat)

    async def send_ads_list(callback, ads_list, cat, subcat=None):
        text = f"<b>Объявления - {cat}"
        if subcat:
            text += f" / {subcat}"
        text += ":</b>\n\n"
        if not ads_list:
            text += "Пока объявлений нет."
            await callback.message.edit_text(text, reply_markup=get_catalog_menu())
            return
        for ad in ads_list:
            ad_text = (
                f"🔹 <b>{ad['title']}</b>\n"
                f"{ad['description']}\n"
                f"<b>Цена:</b> {ad['price']}\n"
                f"<b>Автор:</b> @{ad['username'] if ad['username'] else ad['user_id']}\n"
                f"<code>/ad_{ad['id']}</code>\n\n"
            )
            await callback.message.answer(ad_text, reply_markup=get_ad_menu(ad, callback.from_user.id))
        await callback.message.answer("Вернуться к выбору категорий:", reply_markup=get_catalog_menu())

    @dp.message(F.text.regexp(r"^/ad_(\d+)$"))
    async def msg_view_ad(message: Message):
        ad_id = int(message.text.split("_")[1])
        ad = next((a for a in ads if a["id"] == ad_id), None)
        if not ad:
            await message.answer("Объявление не найдено.")
            return
        ad_text = (
            f"🔹 <b>{ad['title']}</b>\n"
            f"{ad['description']}\n"
            f"<b>Цена:</b> {ad['price']}\n"
            f"<b>Автор:</b> @{ad['username'] if ad['username'] else ad['user_id']}\n"
        )
        await message.answer(ad_text, reply_markup=get_ad_menu(ad, message.from_user.id))

    # Удаление объявлений
    @dp.callback_query(F.data.startswith("delete_"))
    async def cb_delete_ad(callback: CallbackQuery):
        ad_id = int(callback.data.split("_")[1])
        ad = next((a for a in ads if a["id"] == ad_id), None)
        if not ad:
            await callback.answer("Объявление уже удалено.", show_alert=True)
            return
        if callback.from_user.id not in ADMIN_IDS and callback.from_user.id != ad["user_id"]:
            await callback.answer("Удалять объявление может только его владелец или администратор.", show_alert=True)
            return
        ads.remove(ad)
        await callback.message.edit_text("Объявление удалено.", reply_markup=get_main_menu())

    # Назад к выбору категории при создании объявления
    @dp.callback_query(F.data == "choose_category")
    async def cb_choose_category(callback: CallbackQuery, state: FSMContext):
        await state.set_state(AdCreation.category)
        await callback.message.edit_text("Выберите категорию:", reply_markup=get_categories_menu())

    # Обработка всех остальных callback
    @dp.callback_query()
    async def cb_unknown(callback: CallbackQuery):
        await callback.answer("Неизвестная команда.")

    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
