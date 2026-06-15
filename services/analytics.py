"""
Analytics service — Flip Score, ROI, проверка продавца.
v2: учитывает результат relevance check для более точного скора.
"""
from __future__ import annotations

import statistics
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.relevance import RelevanceResult

from parsers.olx_parser import OLXListing

URGENCY_KEYWORDS = ["срочно", "срочна", "терміново", "торг", "торгуюсь", "переїзд",
                    "переезд", "не користуюсь", "не пользуюсь", "потрібно продати",
                    "нужно продать", "уступлю", "знижка", "скидка"]
BOX_KEYWORDS = ["коробка", "коробці", "box", "документи", "документы", "чек",
                "гарантія", "гарантия", "warranty", "комплект", "повний комплект"]
SUSPICIOUS_KEYWORDS = ["предоплата", "передоплата", "аванс", "відправлю", "отправлю",
                       "перевод", "переказ", "безналичные", "нова пошта відправка"]


class AnalyticsService:

    async def get_market_price(self, keyword: str, db_prices: list[float]) -> float:
        """
        Медианная рыночная цена из исторических данных БД.
        Только реальные цены (уже отфильтрованные по релевантности).
        """
        if len(db_prices) < 3:
            return 0.0  # Недостаточно данных — не гадаем

        prices = sorted(db_prices)
        # Убираем топ и боттом 10% выбросов
        if len(prices) >= 10:
            cut = max(1, len(prices) // 10)
            prices = prices[cut:-cut]

        return statistics.median(prices)

    def calculate_roi(self, buy_price: float, market_price: float) -> float:
        if market_price <= 0 or buy_price <= 0:
            return 0.0
        return round((market_price - buy_price) / buy_price * 100, 1)

    def calculate_profit(self, buy_price: float, market_price: float) -> float:
        return max(0.0, round(market_price - buy_price, 2))

    def calculate_flip_score(
        self,
        listing: OLXListing,
        market_price: float,
        db_prices: list[float],
        relevance=None,
    ) -> int:
        score = 0

        if market_price <= 0 or listing.price <= 0:
            return 0

        # ── 1. Скидка к рынку (до 40 очков) ──────────────────────────────────
        discount_pct = (market_price - listing.price) / market_price * 100
        if discount_pct >= 40:
            score += 40
        elif discount_pct >= 30:
            score += 32
        elif discount_pct >= 20:
            score += 22
        elif discount_pct >= 10:
            score += 12
        elif discount_pct >= 5:
            score += 5
        elif discount_pct < 0:
            score -= 15  # дороже рынка

        # ── 2. Срочность (до 15 очков) ────────────────────────────────────────
        text = (listing.title + " " + (listing.description or "")).lower()
        if relevance:
            urgency_hits = len(relevance.urgency_signals)
        else:
            urgency_hits = sum(1 for kw in URGENCY_KEYWORDS if kw in text)
        score += min(urgency_hits * 5, 15)

        # ── 3. Коробка/документы (до 10 очков) ───────────────────────────────
        if relevance:
            box_hits = len(relevance.completeness_signals)
        else:
            box_hits = sum(1 for kw in BOX_KEYWORDS if kw in text)
        score += min(box_hits * 5, 10)

        # ── 4. Возраст аккаунта продавца (до 15 очков) ───────────────────────
        age = self._seller_age_years(listing.seller_created)
        if age >= 3:
            score += 15
        elif age >= 1:
            score += 9
        elif age >= 0.25:
            score += 3
        else:
            score -= 10  # новый аккаунт = высокий риск

        # ── 5. Фото есть (5 очков) ────────────────────────────────────────────
        if listing.photo_url:
            score += 5

        # ── 6. Телефон указан (5 очков) ───────────────────────────────────────
        if listing.phone:
            score += 5

        # ── 7. Достаточно рыночных данных (до 10 очков) ───────────────────────
        if len(db_prices) >= 15:
            score += 10
        elif len(db_prices) >= 7:
            score += 5

        # ── 8. Штраф за подозрительные слова ─────────────────────────────────
        suspicious = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in text)
        score -= suspicious * 15

        return max(0, min(100, score))

    def check_seller(self, listing: OLXListing) -> str:
        age = self._seller_age_years(listing.seller_created)
        text = (listing.title + " " + (listing.description or "")).lower()
        suspicious = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in text)

        if suspicious >= 2:
            return "scammer"
        if age < 0.08:
            return "new"
        if age >= 2:
            return "trusted"
        return "normal"

    def seller_label(self, status: str) -> str:
        return {
            "trusted": "✅ Надёжный продавец",
            "normal": "👤 Обычный продавец",
            "new": "⚠️ Новый аккаунт — будьте осторожны",
            "scammer": "🚫 Возможный мошенник",
        }.get(status, "❓ Неизвестно")

    def _seller_age_years(self, created_str: str) -> float:
        if not created_str:
            return 0.0
        try:
            s = str(created_str)
            if s.isdigit():
                created = datetime.fromtimestamp(int(s))
            else:
                created = datetime.fromisoformat(s.replace("Z", "").replace("+00:00", ""))
            return (datetime.utcnow() - created).days / 365
        except Exception:
            return 0.0

    def smart_labels(
        self,
        listing: OLXListing,
        roi: float,
        flip_score: int,
        profit: float,
        relevance=None,
    ) -> list[str]:
        labels = []
        if flip_score >= 90:
            labels.append("🔥 Горячая сделка")
        if profit >= 5000:
            labels.append("💰 Большая прибыль")
        if roi >= 50:
            labels.append("📈 ROI 50%+")
        if relevance and relevance.urgency_signals:
            labels.append("⚡️ Срочная продажа")
        if relevance and relevance.completeness_signals:
            labels.append("📦 Полный комплект")
        return labels
