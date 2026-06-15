from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models.profit import Profit
from datetime import datetime, timedelta


class ProfitRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, olx_id: str, title: str, buy_price: float) -> Profit:
        p = Profit(user_id=user_id, olx_id=olx_id, title=title, buy_price=buy_price, status="bought")
        self.session.add(p)
        await self.session.commit()
        return p

    async def get_by_user(self, user_id: int, status: str = None) -> list[Profit]:
        q = select(Profit).where(Profit.user_id == user_id)
        if status:
            q = q.where(Profit.status == status)
        result = await self.session.execute(q.order_by(Profit.created_at.desc()))
        return list(result.scalars().all())

    async def mark_sold(self, profit_id: int, sell_price: float) -> bool:
        result = await self.session.execute(
            select(Profit).where(Profit.id == profit_id)
        )
        p = result.scalar_one_or_none()
        if p:
            p.sell_price = sell_price
            p.profit = sell_price - p.buy_price
            p.status = "sold"
            p.sold_at = datetime.utcnow()
            await self.session.commit()
            return True
        return False

    async def get_total_profit(self, user_id: int, since: datetime = None) -> float:
        q = select(func.sum(Profit.profit)).where(Profit.user_id == user_id, Profit.status == "sold")
        if since:
            q = q.where(Profit.sold_at >= since)
        result = await self.session.execute(q)
        return result.scalar() or 0.0
