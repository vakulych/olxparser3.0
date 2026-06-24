from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repo import UserRepository
from database.repositories.search_repo import SearchRepository
from utils.logger import logger

router = Router()


@router.message(Command("searches"))
@router.message(F.text == "🔍 Мои поиски")
async def cmd_searches(message: Message, session: AsyncSession):
    """Список текущих поисков пользователя."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    search_repo = SearchRepository(session)
    searches = await search_repo.get_by_user(message.from_user.id)

    if not searches:
        await message.answer(
            "📋 <b>У вас нет активных поисков</b>\n\n"
            "Используйте ➕ <b>Добавить поиск</b> для создания нового.",
            parse_mode="HTML"
        )
        return

    text = "<b>📋 Ваши поиски:</b>\n\n"
    for search in searches:
        city = f" 📍 {search.city_filter}" if search.city_filter else ""
        text += f"🔹 {search.keyword}{city}\n"

    await message.answer(text, parse_mode="HTML")
