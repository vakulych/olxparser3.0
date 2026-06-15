from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.search_repo import SearchRepository
from bot.keyboards import searches_kb, cancel_kb, main_menu_kb

router = Router()

MAX_SEARCHES = 10

# Популярные города для подсказки
CITY_HINT = "Київ, Харків, Одеса, Дніпро, Львів, Запоріжжя або 'всі міста'"


class SearchStates(StatesGroup):
    waiting_keyword = State()
    waiting_city = State()


@router.message(Command("searches"))
@router.message(F.text == "🔍 Мої пошуки")
@router.message(F.text == "🔍 Мои поиски")
async def cmd_searches(message: Message, session: AsyncSession):
    repo = SearchRepository(session)
    searches = await repo.get_by_user(message.from_user.id)
    if not searches:
        await message.answer(
            "📭 У вас нет активных поисков.\n\nНажмите <b>➕ Добавить поиск</b>",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    lines = [f"🔍 <b>Ваши поиски ({len(searches)}/{MAX_SEARCHES}):</b>\n"]
    for s in searches:
        city = f" 📍 {s.city_filter}" if s.city_filter else " 🌍 все города"
        lines.append(f"• <b>{s.keyword}</b>{city}")

    await message.answer(
        "\n".join(lines),
        reply_markup=searches_kb(searches),
        parse_mode="HTML",
    )


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить поиск")
async def cmd_add_search(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_keyword)
    await message.answer(
        "✏️ <b>Шаг 1/2</b> — введите товар для поиска:\n\n"
        "<i>Примеры: iPhone 15 Pro, PlayStation 5, MacBook Air M2, Дрель Bosch</i>\n\n"
        "💡 Чем точнее запрос — тем меньше мусора.",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


@router.message(SearchStates.waiting_keyword)
async def process_keyword(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_menu_kb())
        return

    keyword = message.text.strip()
    if len(keyword) < 2:
        await message.answer("⚠️ Слишком короткий запрос. Попробуйте ещё раз.")
        return

    repo = SearchRepository(session)
    searches = await repo.get_by_user(message.from_user.id)

    if len(searches) >= MAX_SEARCHES:
        await state.clear()
        await message.answer(
            f"⚠️ Максимум {MAX_SEARCHES} поисков. Сначала удалите ненужные.",
            reply_markup=main_menu_kb(),
        )
        return

    if await repo.exists(message.from_user.id, keyword):
        await state.clear()
        await message.answer(
            f"⚠️ Поиск <b>{keyword}</b> уже добавлен.",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    await state.update_data(keyword=keyword)
    await state.set_state(SearchStates.waiting_city)
    await message.answer(
        f"📍 <b>Шаг 2/2</b> — укажите город:\n\n"
        f"<i>{CITY_HINT}</i>\n\n"
        f"Напишите название города или отправьте <b>всі міста</b> для поиска по всей Украине.",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


@router.message(SearchStates.waiting_city)
async def process_city(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    keyword = data["keyword"]
    city_raw = message.text.strip()

    no_city_phrases = {"всі міста", "все города", "всі", "все", "нет", "ні", "-", "any", "all"}
    city_filter = None if city_raw.lower() in no_city_phrases else city_raw

    repo = SearchRepository(session)
    await repo.add(user_id=message.from_user.id, keyword=keyword, city_filter=city_filter)
    await state.clear()

    city_text = f"📍 {city_filter}" if city_filter else "🌍 все города"
    await message.answer(
        f"✅ Поиск добавлен!\n\n"
        f"🔍 Товар: <b>{keyword}</b>\n"
        f"📍 Город: <b>{city_text}</b>\n\n"
        f"🔔 Буду присылать выгодные объявления в реальном времени.",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data.startswith("search_del:"))
async def delete_search(call: CallbackQuery, session: AsyncSession):
    search_id = int(call.data.split(":")[1])
    repo = SearchRepository(session)
    deleted = await repo.delete(search_id, call.from_user.id)
    if deleted:
        await call.answer("🗑 Поиск удалён")
        searches = await repo.get_by_user(call.from_user.id)
        if searches:
            await call.message.edit_reply_markup(reply_markup=searches_kb(searches))
        else:
            await call.message.edit_text("📭 Нет активных поисков.")
    else:
        await call.answer("❌ Ошибка", show_alert=True)
