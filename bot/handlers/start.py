from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repo import UserRepository
from bot.keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    repo = UserRepository(session)
    await repo.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "",
    )
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "🤖 Я <b>OLX Bot</b> — ищу выгодные сделки для перепродажи.\n\n"
        "📌 Добавь поисковый запрос и получай уведомления о товарах ниже рынка!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
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
async def back_main(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("🏠 Главное меню", reply_markup=main_menu_kb())
    await call.answer()
