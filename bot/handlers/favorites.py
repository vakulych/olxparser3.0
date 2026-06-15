from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repo import UserRepository
from database.repositories.ad_sent_repo import AdSentRepository
from utils.logger import logger

router = Router()


@router.message(Command("favorites"))
@router.message(F.text == "⭐️ Избранное")
async def cmd_favorites(message: Message, session: AsyncSession):
    """Просмотр избранного."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    ads = await ad_sent_repo.get_all_for_user(message.from_user.id, limit=100)

    if not ads:
        await message.answer(
            "📋 <b>Избранного еще нет</b>\n\n"
            "При получении сделок используйте ⭐️ для добавления в избранное.",
            parse_mode="HTML"
        )
        return

    text = "<b>⭐️ Ваше избранное:</b>\n\n"
    for ad in ads[:20]:  # Показываем последние 20
        text += f"🔹 {ad.title}\n💰 {ad.price:,.0f} грн\n🔗 {ad.url}\n\n"

    await message.answer(text, parse_mode="HTML")
