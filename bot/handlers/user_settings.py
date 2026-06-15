from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repo import UserRepository
from bot.keyboards import settings_kb, cancel_kb, main_menu_kb

router = Router()

SETTING_LABELS = {
    "min_profit": ("💰 Мин. прибыль (грн)", float),
    "min_roi": ("📊 Мин. ROI (%)", float),
    "max_price": ("💸 Макс. цена (грн)", float),
    "city": ("📍 Город (или 'нет' для отключения)", str),
    "keywords_bl": ("🚫 Стоп-слова (через запятую)", str),
    "sellers_bl": ("👤 Стоп-продавцы (через запятую)", str),
}

DB_FIELD_MAP = {
    "min_profit": "min_profit",
    "min_roi": "min_roi",
    "max_price": "max_price",
    "city": "city_filter",
    "keywords_bl": "keyword_blacklist",
    "sellers_bl": "seller_blacklist",
}


class SettingsStates(StatesGroup):
    waiting_value = State()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: Message, session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    text = (
        "⚙️ <b>Ваши настройки:</b>\n\n"
        f"💰 Мин. прибыль: <b>{user.min_profit:,.0f} грн</b>\n"
        f"📊 Мин. ROI: <b>{user.min_roi:.1f}%</b>\n"
        f"💸 Макс. цена: <b>{user.max_price:,.0f} грн</b>\n"
        f"📍 Город: <b>{user.city_filter or 'не задан'}</b>\n"
        f"🚫 Стоп-слова: <b>{user.keyword_blacklist or 'нет'}</b>\n"
        f"👤 Стоп-продавцы: <b>{user.seller_blacklist or 'нет'}</b>"
    )
    await message.answer(text, reply_markup=settings_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("set:"))
async def setting_start(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    label, _ = SETTING_LABELS[key]
    await state.update_data(setting_key=key)
    await state.set_state(SettingsStates.waiting_value)
    await call.message.answer(f"✏️ Введите новое значение для <b>{label}</b>:", parse_mode="HTML", reply_markup=cancel_kb())
    await call.answer()


@router.message(SettingsStates.waiting_value)
async def setting_value(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    key = data["setting_key"]
    _, cast = SETTING_LABELS[key]
    db_field = DB_FIELD_MAP[key]

    try:
        value = cast(message.text.strip()) if cast != str else message.text.strip()
        if db_field == "city_filter" and value.lower() == "нет":
            value = None
    except ValueError:
        await message.answer("⚠️ Неверный формат. Попробуйте ещё раз.")
        return

    repo = UserRepository(session)
    await repo.update_settings(message.from_user.id, **{db_field: value})
    await state.clear()
    await message.answer(f"✅ Настройка сохранена!", reply_markup=main_menu_kb())
