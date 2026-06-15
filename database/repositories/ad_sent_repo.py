from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.ad_sent import AdSent
from datetime import datetime, timedelta


class AdSentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ad_sent: AdSent) -> AdSent:
        """Сохранить отправленный товар для пользователя."""
        self.session.add(ad_sent)
        await self.session.flush()
        return ad_sent

    async def exists_for_user(self, user_id: int, olx_id: str) -> bool:
        """Проверить, отправлен ли этот товар этому пользователю."""
        query = select(AdSent).where(
            and_(AdSent.user_id == user_id, AdSent.olx_id == olx_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def get_all_for_user(self, user_id: int, limit: int = 100) -> list[AdSent]:
        """Получить все отправленные товары пользователя."""
        query = select(AdSent).where(
            AdSent.user_id == user_id
        ).order_by(
            AdSent.sent_at.desc()
        ).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_period_for_user(
        self, user_id: int, days: int = 7
    ) -> list[AdSent]:
        """Получить товары за последние N дней для пользователя."""
        since = datetime.utcnow() - timedelta(days=days)
        query = select(AdSent).where(
            and_(
                AdSent.user_id == user_id,
                AdSent.sent_at >= since
            )
        ).order_by(
            AdSent.sent_at.desc()
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_stats_for_user(self, user_id: int, days: int = 30) -> dict:
        """Получить статистику для пользователя."""
        since = datetime.utcnow() - timedelta(days=days)
        query = select(AdSent).where(
            and_(
                AdSent.user_id == user_id,
                AdSent.sent_at >= since
            )
        )
        result = await self.session.execute(query)
        ads = result.scalars().all()

        if not ads:
            return {
                "total_deals": 0,
                "total_profit": 0.0,
                "avg_roi": 0.0,
                "best_deal_profit": 0.0,
            }

        total_profit = sum(ad.profit for ad in ads)
        total_roi_sum = sum(ad.roi for ad in ads)
        avg_roi = total_roi_sum / len(ads) if ads else 0.0
        best_profit = max((ad.profit for ad in ads), default=0.0)

        return {
            "total_deals": len(ads),
            "total_profit": total_profit,
            "avg_roi": avg_roi,
            "best_deal_profit": best_profit,
        }
