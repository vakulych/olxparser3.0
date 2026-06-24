from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.user_repo import UserRepository
from database.repositories.ad_sent_repo import AdSentRepository
from services.export_service import export_to_csv, export_to_excel, export_to_json
from io import BytesIO
import tempfile
from utils.logger import logger

router = Router()


@router.message(Command("export"))
@router.message(F.text == "📤 Экспорт")
async def cmd_export(message: Message, session: AsyncSession):
    """Экспорт данных пользователя."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    ads = await ad_sent_repo.get_all_for_user(message.from_user.id, limit=1000)

    if not ads:
        await message.answer(
            "📋 <b>Нет данных для экспорта</b>\n\n"
            "Вы еще не получили ни одной сделки.",
            parse_mode="HTML"
        )
        return

    # Предложить форматы
    text = (
        "<b>📤 Выберите формат экспорта:</b>\n\n"
        "🔹 /export_csv - CSV файл\n"
        "🔹 /export_excel - Excel файл\n"
        "🔹 /export_json - JSON файл"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("export_csv"))
async def export_csv(message: Message, session: AsyncSession):
    """Экспорт в CSV."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    ads = await ad_sent_repo.get_all_for_user(message.from_user.id, limit=1000)

    csv_data = export_to_csv(ads)
    
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(csv_data)
        tmp.flush()
        file = FSInputFile(tmp.name)
        await message.answer_document(file, caption="📊 Ваш экспорт в CSV")
        logger.info(f"User {message.from_user.id} exported CSV")


@router.message(Command("export_excel"))
async def export_excel(message: Message, session: AsyncSession):
    """Экспорт в Excel."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    ads = await ad_sent_repo.get_all_for_user(message.from_user.id, limit=1000)

    excel_data = export_to_excel(ads)
    
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(excel_data)
        tmp.flush()
        file = FSInputFile(tmp.name)
        await message.answer_document(file, caption="📊 Ваш экспорт в Excel")
        logger.info(f"User {message.from_user.id} exported Excel")


@router.message(Command("export_json"))
async def export_json(message: Message, session: AsyncSession):
    """Экспорт в JSON."""
    repo = UserRepository(session)
    user = await repo.get(message.from_user.id)
    
    if not user or not user.is_active:
        await message.answer("❌ <b>Доступ не предоставлен</b>", parse_mode="HTML")
        return

    ad_sent_repo = AdSentRepository(session)
    ads = await ad_sent_repo.get_all_for_user(message.from_user.id, limit=1000)

    json_data = export_to_json(ads)
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(json_data)
        tmp.flush()
        file = FSInputFile(tmp.name)
        await message.answer_document(file, caption="📊 Ваш экспорт в JSON")
        logger.info(f"User {message.from_user.id} exported JSON")
