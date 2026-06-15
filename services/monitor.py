"""
Monitor service — фоновый мониторинг OLX.

Ключевые улучшения v2:
- Нет задержек между запросами (антибан теперь только на уровне парсера)
- Умная фильтрация релевантности (чехлы/стекла отсеиваются)
- Sanity-check цены (125 грн за iPhone = мусор)
- Фильтр города per-search
- Правильный расчёт рыночной цены (только от релевантных объявлений)
"""
from __future__ import annotations

import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from parsers.olx_parser import OLXParser, OLXListing
from services.analytics import AnalyticsService
from services.relevance import check_relevance, is_price_realistic
from database.engine import AsyncSessionFactory
from database.models.ad import Ad
from database.repositories.user_repo import UserRepository
from database.repositories.search_repo import SearchRepository
from database.repositories.ad_repo import AdRepository
from config.settings import settings
from utils.logger import logger


def seller_age_human(created_str: str) -> str:
    from datetime import datetime
    if not created_str:
        return "неизвестно"
    try:
        if str(created_str).isdigit():
            created = datetime.fromtimestamp(int(created_str))
        else:
            created = datetime.fromisoformat(str(created_str).replace("Z", "").replace("+00:00", ""))
        delta = datetime.utcnow() - created
        years = delta.days // 365
        months = (delta.days % 365) // 30
        if years >= 1:
            return f"{years} {'год' if years == 1 else 'лет'}"
        return f"{months} мес." if months > 0 else "< 1 мес."
    except Exception:
        return "неизвестно"


def format_notification(
    listing: OLXListing,
    market_price: float,
    profit: float,
    roi: float,
    flip_score: int,
    seller_label: str,
    seller_age: str,
    smart_labels: list[str],
    search_keyword: str,
) -> str:
    if flip_score >= 90:
        header = "🔥 ГОРЯЧАЯ СДЕЛКА!"
        score_emoji = "🔥"
    elif flip_score >= 75:
        header = "⭐️ Выгодное объявление"
        score_emoji = "⭐️"
    else:
        header = "📦 Новое объявление"
        score_emoji = "📊"

    labels_str = "  ".join(smart_labels) if smart_labels else ""

    lines = [
        f"{header}",
        "",
        f"📦 <b>{listing.title}</b>",
        f"🔍 Запрос: <i>{search_keyword}</i>",
        f"📍 <b>{listing.city or 'город не указан'}</b>",
        "",
        f"💰 Цена: <b>{listing.price:,.0f} грн</b>",
    ]

    if market_price > 0 and market_price != listing.price * 1.25:
        lines += [
            f"📈 Рынок: {market_price:,.0f} грн",
            f"💵 Прибыль: <b>{profit:,.0f} грн</b>",
            f"📊 ROI: <b>{roi:.1f}%</b>",
        ]

    lines += [
        f"{score_emoji} Flip Score: <b>{flip_score}/100</b>",
        "",
        f"👤 {listing.seller_name}  🕐 {seller_age}",
        f"{seller_label}",
    ]

    if labels_str:
        lines.append(f"\n{labels_str}")

    lines += ["", f"🔗 {listing.url}"]

    return "\n".join(lines)


class MonitorService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.parser = OLXParser()
        self.analytics = AnalyticsService()

    async def run_cycle(self) -> None:
        logger.info("⏱ Monitor cycle started")

        async with AsyncSessionFactory() as session:
            search_repo = SearchRepository(session)
            user_repo = UserRepository(session)
            ad_repo = AdRepository(session)

            searches = await search_repo.get_all_active()
            if not searches:
                return

            # Группируем по keyword, но сохраняем city_filter каждого пользователя
            # keyword -> list of (user_id, city_filter)
            keyword_map: dict[str, list[tuple[int, str | None]]] = {}
            for s in searches:
                kw = s.keyword.strip().lower()
                keyword_map.setdefault(kw, []).append((s.user_id, s.city_filter))

            tasks = [
                self._process_keyword(kw, subscribers, ad_repo, user_repo, kw)
                for kw, subscribers in keyword_map.items()
            ]
            # Запускаем все ключевые слова параллельно (парсер сам регулирует частоту)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_keyword(
        self,
        keyword: str,
        subscribers: list[tuple[int, str | None]],
        ad_repo: AdRepository,
        user_repo: UserRepository,
        original_keyword: str,
    ) -> None:
        try:
            listings = await self.parser.search(keyword, limit=25)
        except Exception as e:
            logger.error(f"Parser error for '{keyword}': {e}")
            return

        if not listings:
            return

        # Получаем цены ТОЛЬКО релевантных объявлений из БД для расчёта рынка
        db_prices = await ad_repo.get_prices_for_keyword(keyword, days=14)

        for listing in listings:
            # ── Уже видели это объявление? ────────────────────────────────────
            if await ad_repo.exists(listing.olx_id):
                continue

            # ── Проверка релевантности ─────────────────────────────────────────
            relevance = check_relevance(
                query=original_keyword,
                title=listing.title,
                description=listing.description,
                price=listing.price,
            )

            if not relevance.is_relevant:
                logger.debug(f"SKIP [{listing.olx_id}] '{listing.title[:50]}' — {relevance.reason}")
                # Сохраняем в БД но НЕ отправляем
                await self._save_ad(ad_repo, listing, keyword, 0, 0, 0, 0, "irrelevant", skip=True)
                continue

            # ── Расчёт рыночной цены ──────────────────────────────────────────
            market_price = await self.analytics.get_market_price(keyword, db_prices)

            # Sanity check: если рынок посчитался от мусора — он будет аномален
            price_ok, price_reason = is_price_realistic(listing.price, keyword, market_price)
            if not price_ok:
                logger.debug(f"SKIP [{listing.olx_id}] '{listing.title[:50]}' — {price_reason}")
                await self._save_ad(ad_repo, listing, keyword, 0, 0, 0, 0, "bad_price", skip=True)
                continue

            # Если рыночных данных нет — не гадаем, не отправляем фейковый ROI
            if market_price <= 0:
                # Первые объявления накапливаем без уведомлений
                await self._save_ad(ad_repo, listing, keyword, 0, 0, 0, 30, "accumulating")
                db_prices.append(listing.price)  # добавляем в локальный пул
                continue

            profit = self.analytics.calculate_profit(listing.price, market_price)
            roi = self.analytics.calculate_roi(listing.price, market_price)
            flip_score = self.analytics.calculate_flip_score(
                listing, market_price, db_prices, relevance
            )
            seller_status = self.analytics.check_seller(listing)
            seller_label = self.analytics.seller_label(seller_status)
            smart_labels = self.analytics.smart_labels(listing, roi, flip_score, profit, relevance)

            await self._save_ad(ad_repo, listing, keyword, market_price, profit, roi, flip_score, seller_status)
            db_prices.append(listing.price)

            if flip_score < settings.MIN_FLIP_SCORE:
                continue

            message = format_notification(
                listing=listing,
                market_price=market_price,
                profit=profit,
                roi=roi,
                flip_score=flip_score,
                seller_label=seller_label,
                seller_age=seller_age_human(listing.seller_created),
                smart_labels=smart_labels,
                search_keyword=original_keyword,
            )

            for user_id, city_filter in subscribers:
                user = await user_repo.get(user_id)
                if not user or not user.is_active:
                    continue

                # ── Фильтры пользователя ──────────────────────────────────────
                if profit < user.min_profit:
                    continue
                if roi < user.min_roi:
                    continue
                if listing.price > user.max_price:
                    continue

                # Фильтр города: сначала per-search, потом глобальный
                effective_city = city_filter or user.city_filter
                if effective_city and listing.city:
                    if effective_city.lower() not in listing.city.lower():
                        continue

                # Стоп-слова
                bl_words = [w.strip().lower() for w in user.keyword_blacklist.split(",") if w.strip()]
                if any(w in listing.title.lower() for w in bl_words):
                    continue

                bl_sellers = [s.strip().lower() for s in user.seller_blacklist.split(",") if s.strip()]
                if listing.seller_name and listing.seller_name.lower() in bl_sellers:
                    continue

                # Скипаем мошенников
                if seller_status == "scammer":
                    continue

                await self._send(user_id, message)

    async def _save_ad(
        self, repo: AdRepository, listing: OLXListing, keyword: str,
        market_price: float, profit: float, roi: float, flip_score: int,
        seller_status: str, skip: bool = False,
    ) -> None:
        try:
            ad = Ad(
                olx_id=listing.olx_id,
                title=listing.title,
                description=listing.description[:500] if listing.description else "",
                price=listing.price,
                currency=listing.currency,
                url=listing.url,
                city=listing.city,
                photo_url=listing.photo_url,
                seller_name=listing.seller_name,
                seller_id=listing.seller_id,
                seller_created=listing.seller_created,
                market_price=market_price,
                profit=profit,
                roi=roi,
                flip_score=flip_score,
                seller_status=seller_status,
                keyword=keyword,
                is_sent=not skip,
            )
            await repo.save(ad)
        except Exception as e:
            logger.error(f"Save ad error: {e}")

    async def _send(self, user_id: int, text: str) -> None:
        try:
            await self.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} blocked the bot")
        except TelegramBadRequest as e:
            logger.error(f"Bad request to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Send error to {user_id}: {e}")
