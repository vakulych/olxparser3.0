from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, olx_id: str, title: str, url: str, price: float) -> Favorite:
        fav = Favorite(user_id=user_id, olx_id=olx_id, title=title, url=url, price=price)
        self.session.add(fav)
        await self.session.commit()
        return fav

    async def get_by_user(self, user_id: int) -> list[Favorite]:
        result = await self.session.execute(
            select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def remove(self, favorite_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            delete(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == user_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, user_id: int, olx_id: str) -> bool:
        result = await self.session.execute(
            select(Favorite.id).where(Favorite.user_id == user_id, Favorite.olx_id == olx_id)
        )
        return result.scalar_one_or_none() is not None
