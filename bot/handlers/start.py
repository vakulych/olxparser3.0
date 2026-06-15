from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repo import UserRepository
from bot.keyboards import main_menu_kb
from utils.logger import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Команда /start с проверкой доступа."""
    repo = UserRepository(session)
    user = await repo.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "",
    )
    await session.commit()

    # ✅ КРИТИЧНО: Проверка доступа
    if not user.is_active:
        await message.answer(
            f"❌ <b>Доступ не предоставлен</b>\n\n"
            f"Причина: {user.access_denied_reason}\n\n"
            f"ID вашего аккаунта: <code>{message.from_user.id}</code>\n\n"
            f"Свяжитесь с администратором для активации доступа.",
            parse_mode="HTML",
        )
        logger.warning(f"Access denied for user {message.from_user.id}")
        return

    # Если доступ есть
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"✅ <b>Доступ активирован!</b>\n\n"
        f"🤖 Я <b>OLX Bot</b> — ищу выгодные сделки для перепродажи.\n\n"
        f"📌 Добавь поисковый запрос и получай уведомления о товарах ниже рынка!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
    logger.info(f"User {message.from_user.id} started with access")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message, session: AsyncSession):
    """Справка по командам."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer(
            "❌ <b>Доступ не предоставлен</b>",
            parse_mode="HTML",
        )
        return

    text = (
        "📖 <b>Команды бота:</b>\n\n"
        "/start — главное меню\n"
        "/searches — мои поиски\n"
        "/add <i>слово</i> — добавить поиск\n"
        "/favorite — избранное\n"
        "/stats — статистика\n"
        "/settings — настройки\n"
        "/export — экспорт данных\n\n"
        "⭐ <b>Flip Score</b> — оценка выгодности сделки (0–100):\n"
        "95–100 🔥 Отличная\n"
        "80–95 ⭐️ Хорошая\n"
        "60–80 📊 Средняя\n"
        "< 60 — не отправляю"
    )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, session: AsyncSession):
    """Вернуться в главное меню."""
    repo = UserRepository(session)
    user = await repo.get(call.from_user.id)
    
    if not user or not user.is_active:
        await call.answer("❌ Доступ не предоставлен")
        return

    await call.message.delete()
    await call.message.answer("🏠 Главное меню", reply_markup=main_menu_kb())
    await call.answer()
