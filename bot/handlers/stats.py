from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from database.repositories.ad_repo import AdRepository
from database.repositories.profit_repo import ProfitRepository
from bot.keyboards import main_menu_kb

router = Router()


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, session: AsyncSession):
    ad_repo = AdRepository(session)
    profit_repo = ProfitRepository(session)

    stats = await ad_repo.get_stats()
    now = datetime.utcnow()

    profit_day = await profit_repo.get_total_profit(message.from_user.id, since=now - timedelta(days=1))
    profit_week = await profit_repo.get_total_profit(message.from_user.id, since=now - timedelta(weeks=1))
    profit_month = await profit_repo.get_total_profit(message.from_user.id, since=now - timedelta(days=30))
    profit_total = await profit_repo.get_total_profit(message.from_user.id)

    text = (
        "📊 <b>Статистика</b>\n\n"
        "📦 <b>Найдено сделок:</b>\n"
        f"  За день: {stats['today']}\n"
        f"  За неделю: {stats['week']}\n"
        f"  За месяц: {stats['month']}\n"
        f"  Всего: {stats['total']}\n\n"
        "💰 <b>Ваша прибыль:</b>\n"
        f"  За день: {profit_day:,.0f} грн\n"
        f"  За неделю: {profit_week:,.0f} грн\n"
        f"  За месяц: {profit_month:,.0f} грн\n"
        f"  Всего: {profit_total:,.0f} грн"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
