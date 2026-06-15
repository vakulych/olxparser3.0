from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.profit import Profit
from datetime import datetime, timedelta


class ProfitRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, user_id: int, olx_id: str, purchase_price: float, sale_price: float, notes: str = "") -> Profit:
        profit = sale_price - purchase_price
        p = Profit(
            user_id=user_id,
            olx_id=olx_id,
            purchase_price=purchase_price,
            sale_price=sale_price,
            profit=profit,
            notes=notes
        )
        self.session.add(p)
        await self.session.flush()
        return p

    async def get_total_profit(self, user_id: int, days: int = 30) -> float:
        since = datetime.utcnow() - timedelta(days=days)
        query = select(Profit).where(
            (Profit.user_id == user_id) & (Profit.created_at >= since)
        )
        result = await self.session.execute(query)
        profits = result.scalars().all()
        return sum(p.profit for p in profits)

    async def get_by_period(self, user_id: int, days: int = 30) -> list[Profit]:
        since = datetime.utcnow() - timedelta(days=days)
        query = select(Profit).where(
            (Profit.user_id == user_id) & (Profit.created_at >= since)
        ).order_by(Profit.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
