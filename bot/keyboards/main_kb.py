from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔍 Мои поиски"),
        KeyboardButton(text="➕ Добавить поиск"),
    )
    builder.row(
        KeyboardButton(text="⭐ Избранное"),
        KeyboardButton(text="📊 Статистика"),
    )
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="📤 Экспорт"),
    )
    builder.row(KeyboardButton(text="ℹ️ Помощь"))
    return builder.as_markup(resize_keyboard=True)


def searches_kb(searches: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in searches:
        builder.row(
            InlineKeyboardButton(text=f"🔎 {s.keyword}", callback_data=f"search_info:{s.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"search_del:{s.id}"),
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def favorites_kb(favorites: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        builder.row(
            InlineKeyboardButton(text=f"📦 {fav.title[:30]}", url=fav.url),
            InlineKeyboardButton(text="🗑", callback_data=f"fav_del:{fav.id}"),
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def export_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Excel", callback_data="export:excel"),
        InlineKeyboardButton(text="📄 CSV", callback_data="export:csv"),
        InlineKeyboardButton(text="🗃 JSON", callback_data="export:json"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Мин. прибыль", callback_data="set:min_profit"))
    builder.row(InlineKeyboardButton(text="📊 Мин. ROI", callback_data="set:min_roi"))
    builder.row(InlineKeyboardButton(text="💸 Макс. цена", callback_data="set:max_price"))
    builder.row(InlineKeyboardButton(text="📍 Фильтр города", callback_data="set:city"))
    builder.row(InlineKeyboardButton(text="🚫 Стоп-слова", callback_data="set:keywords_bl"))
    builder.row(InlineKeyboardButton(text="👤 Стоп-продавцы", callback_data="set:sellers_bl"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)
