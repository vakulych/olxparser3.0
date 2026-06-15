from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from config.settings import settings
from database.models.user import User
from database.repositories.ad_repo import AdRepository
from bot.keyboards import main_menu_kb
from utils.logger import logger

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 Нет доступа.")
        return
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "/users — список пользователей\n"
        "/logs — последние логи\n"
        "/broadcast <i>текст</i> — рассылка всем",
        parse_mode="HTML",
    )


@router.message(Command("users"))
async def cmd_users(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    result = await session.execute(select(func.count(User.id)))
    total = result.scalar()
    result2 = await session.execute(select(func.count(User.id)).where(User.is_active == True))
    active = result2.scalar()
    await message.answer(
        f"👥 <b>Пользователи</b>\n\nВсего: {total}\nАктивных: {active}",
        parse_mode="HTML",
    )


@router.message(Command("logs"))
async def cmd_logs(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        with open("logs/bot.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-30:]
        text = "".join(lines)[-3800:]
        await message.answer(f"<pre>{text}</pre>", parse_mode="HTML")
    except FileNotFoundError:
        await message.answer("📭 Лог-файл не найден.")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст>")
        return

    result = await session.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()

    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user.id, text)
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {user.id}: {e}")

    await message.answer(f"✅ Рассылка отправлена {sent}/{len(users)} пользователям.")
