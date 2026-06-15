from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.ad import Ad
from datetime import datetime, timedelta


class AdRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ad: Ad) -> Ad:
        self.session.add(ad)
        await self.session.flush()
        return ad

    async def exists(self, olx_id: str) -> bool:
        query = select(Ad).where(Ad.olx_id == olx_id)
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def get_prices_for_keyword(self, keyword: str, days: int = 14) -> list[float]:
        since = datetime.utcnow() - timedelta(days=days)
        query = select(Ad.price).where(
            and_(
                Ad.keyword == keyword,
                Ad.is_sent == True,
                Ad.created_at >= since,
                Ad.market_price > 0
            )
        )
        result = await self.session.execute(query)
        prices = result.scalars().all()
        return prices if prices else []
