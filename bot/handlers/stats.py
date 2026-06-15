from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repo import UserRepository
from database.repositories.ad_sent_repo import AdSentRepository
from utils.logger import logger

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, session: AsyncSession):
    """Статистика пользователя."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    
    # За различные периоды
    stats_day = await ad_sent_repo.get_stats_for_user(message.from_user.id, days=1)
    stats_week = await ad_sent_repo.get_stats_for_user(message.from_user.id, days=7)
    stats_month = await ad_sent_repo.get_stats_for_user(message.from_user.id, days=30)
    
    text = (
        "<b>📊 Ваша статистика:</b>\n\n"
        f"<b>За день:</b>\n"
        f"  🎯 Найдено сделок: {stats_day['total_deals']}\n"
        f"  💵 Сумма прибыли: {stats_day['total_profit']:,.0f} грн\n"
        f"  📈 Средний ROI: {stats_day['avg_roi']:.1f}%\n\n"
        f"<b>За неделю:</b>\n"
        f"  🎯 Найдено сделок: {stats_week['total_deals']}\n"
        f"  💵 Сумма прибыли: {stats_week['total_profit']:,.0f} грн\n"
        f"  📈 Средний ROI: {stats_week['avg_roi']:.1f}%\n\n"
        f"<b>За месяц:</b>\n"
        f"  🎯 Найдено сделок: {stats_month['total_deals']}\n"
        f"  💵 Сумма прибыли: {stats_month['total_profit']:,.0f} грн\n"
        f"  📈 Средний ROI: {stats_month['avg_roi']:.1f}%"
    )
    await message.answer(text, parse_mode="HTML")
