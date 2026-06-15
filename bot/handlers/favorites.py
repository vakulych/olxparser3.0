from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.favorite_repo import FavoriteRepository
from bot.keyboards import favorites_kb, main_menu_kb

router = Router()


@router.message(Command("favorite"))
@router.message(F.text == "⭐ Избранное")
async def cmd_favorites(message: Message, session: AsyncSession):
    repo = FavoriteRepository(session)
    favs = await repo.get_by_user(message.from_user.id)
    if not favs:
        await message.answer("⭐ Избранное пусто.", reply_markup=main_menu_kb())
        return
    await message.answer(
        f"⭐ <b>Избранное ({len(favs)}):</b>",
        reply_markup=favorites_kb(favs),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fav_del:"))
async def delete_favorite(call: CallbackQuery, session: AsyncSession):
    fav_id = int(call.data.split(":")[1])
    repo = FavoriteRepository(session)
    deleted = await repo.remove(fav_id, call.from_user.id)
    if deleted:
        await call.answer("🗑 Удалено из избранного")
        favs = await repo.get_by_user(call.from_user.id)
        if favs:
            await call.message.edit_reply_markup(reply_markup=favorites_kb(favs))
        else:
            await call.message.edit_text("⭐ Избранное пусто.")
    else:
        await call.answer("❌ Ошибка", show_alert=True)
