import io
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.ad_repo import AdRepository
from services.export_service import export_to_csv, export_to_excel, export_to_json
from bot.keyboards import export_kb, main_menu_kb

router = Router()


@router.message(Command("export"))
@router.message(F.text == "📤 Экспорт")
async def cmd_export(message: Message):
    await message.answer("📤 Выберите формат экспорта:", reply_markup=export_kb())


@router.callback_query(F.data.startswith("export:"))
async def do_export(call: CallbackQuery, session: AsyncSession):
    fmt = call.data.split(":")[1]
    await call.answer("⏳ Подготавливаю файл...")

    repo = AdRepository(session)
    ads = await repo.get_recent(limit=500)

    if not ads:
        await call.message.answer("📭 Нет данных для экспорта.", reply_markup=main_menu_kb())
        return

    if fmt == "csv":
        data = export_to_csv(ads)
        file = BufferedInputFile(data, filename="olx_deals.csv")
        await call.message.answer_document(file, caption=f"📄 CSV — {len(ads)} записей")
    elif fmt == "excel":
        data = export_to_excel(ads)
        file = BufferedInputFile(data, filename="olx_deals.xlsx")
        await call.message.answer_document(file, caption=f"📊 Excel — {len(ads)} записей")
    elif fmt == "json":
        data = export_to_json(ads)
        file = BufferedInputFile(data, filename="olx_deals.json")
        await call.message.answer_document(file, caption=f"🗃 JSON — {len(ads)} записей")
