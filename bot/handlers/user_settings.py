from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repo import UserRepository
from utils.logger import logger

router = Router()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: Message, session: AsyncSession):
    """Просмотр и редактирование настроек."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    text = (
        "<b>⚙️ Ваши настройки:</b>\n\n"
        f"<b>Фильтры:</b>\n"
        f"💵 Минимальная прибыль: {user.min_profit:,.0f} грн\n"
        f"📈 Минимальный ROI: {user.min_roi:.1f}%\n"
        f"💰 Максимальная цена: {user.max_price:,.0f} грн\n"
        f"📍 Город: {user.city_filter or 'любой'}\n\n"
        f"<b>Черные списки:</b>\n"
        f"🚫 Стоп-слова: {user.keyword_blacklist if user.keyword_blacklist else 'не указаны'}\n"
        f"🚫 Черный список продавцов: {user.seller_blacklist if user.seller_blacklist else 'не указаны'}\n"
    )
    await message.answer(text, parse_mode="HTML")
