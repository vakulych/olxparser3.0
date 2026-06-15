from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models.ad import Ad
from typing import Optional
from datetime import datetime, timedelta


class AdRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, olx_id: str) -> bool:
        result = await self.session.execute(
            select(Ad.id).where(Ad.olx_id == olx_id)
        )
        return result.scalar_one_or_none() is not None

    async def save(self, ad: Ad) -> Ad:
        self.session.add(ad)
        await self.session.commit()
        await self.session.refresh(ad)
        return ad

    async def get_recent(self, limit: int = 50) -> list[Ad]:
        result = await self.session.execute(
            select(Ad).order_by(Ad.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self, user_id: int = None) -> dict:
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)
        month_ago = now - timedelta(days=30)

        async def count_since(since: datetime) -> int:
            result = await self.session.execute(
                select(func.count(Ad.id)).where(Ad.created_at >= since)
            )
            return result.scalar() or 0

        return {
            "today": await count_since(day_ago),
            "week": await count_since(week_ago),
            "month": await count_since(month_ago),
            "total": (await self.session.execute(select(func.count(Ad.id)))).scalar() or 0,
        }

    async def get_prices_for_keyword(self, keyword: str, days: int = 7) -> list[float]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Ad.price).where(
                Ad.keyword.ilike(f"%{keyword}%"),
                Ad.price > 0,
                Ad.created_at >= since,
            )
        )
        return [row[0] for row in result.fetchall()]
