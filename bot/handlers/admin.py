from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repo import UserRepository
from config.settings import settings
from utils.logger import logger

router = Router()


@router.message(Command("admin_grant"))
async def admin_grant_access(message: Message, session: AsyncSession):
    """Дать доступ пользователю. /admin_grant USER_ID"""
    # Только админы
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Только администратор")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Использование: /admin_grant USER_ID\n"
            "Пример: /admin_grant 123456789"
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID должен быть числом")
        return

    repo = UserRepository(session)
    user = await repo.grant_access(user_id)
    await session.commit()

    if user:
        await message.answer(
            f"✅ <b>Доступ выдан пользователю {user_id}</b>\n"
            f"Имя: {user.full_name}\n"
            f"Username: @{user.username or 'не указан'}"
        )
        logger.info(f"Admin {message.from_user.id} granted access to {user_id}")
        
        # Уведомляем пользователя
        try:
            from aiogram import Bot
            from config.settings import settings
            bot = Bot(token=settings.BOT_TOKEN)
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 <b>ДОСТУП К БОТУ ВЫДАН!</b>\n\n"
                    "Вы получили доступ к OLX Bot. Теперь вы можете:\n\n"
                    "✅ Добавлять поисковые запросы\n"
                    "✅ Получать уведомления о выгодных сделках\n"
                    "✅ Отслеживать прибыль\n\n"
                    "Используйте /start для начала работы."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")
    else:
        await message.answer(f"❌ Пользователь {user_id} не найден")


@router.message(Command("admin_revoke"))
async def admin_revoke_access(message: Message, session: AsyncSession):
    """Отозвать доступ пользователя. /admin_revoke USER_ID"""
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Только администратор")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Использование: /admin_revoke USER_ID\n"
            "Пример: /admin_revoke 123456789"
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ USER_ID должен быть числом")
        return

    repo = UserRepository(session)
    user = await repo.revoke_access(user_id, "Доступ отозван администратором")
    await session.commit()

    if user:
        await message.answer(
            f"🚫 <b>Доступ отозван у пользователя {user_id}</b>\n"
            f"Имя: {user.full_name}"
        )
        logger.warning(f"Admin {message.from_user.id} revoked access from {user_id}")
    else:
        await message.answer(f"❌ Пользователь {user_id} не найден")


@router.message(Command("admin_list"))
async def admin_list_users(message: Message, session: AsyncSession):
    """Список пользователей."""
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Только администратор")
        return

    repo = UserRepository(session)
    query = select(User).order_by(User.created_at.desc()).limit(20)
    result = await session.execute(query)
    users = result.scalars().all()

    if not users:
        await message.answer("Нет пользователей в системе")
        return

    text = "<b>📋 Список пользователей:</b>\n\n"
    for user in users:
        status = "✅ АКТИВЕН" if user.is_active else "❌ БЕЗ ДОСТУПА"
        text += f"ID: <code>{user.id}</code>\n{user.full_name} (@{user.username})\n{status}\n\n"

    await message.answer(text, parse_mode="HTML")
