from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, olx_id: str, title: str) -> Favorite:
        favorite = Favorite(user_id=user_id, olx_id=olx_id, title=title)
        self.session.add(favorite)
        await self.session.flush()
        return favorite

    async def remove(self, user_id: int, olx_id: str) -> bool:
        query = select(Favorite).where(
            (Favorite.user_id == user_id) & (Favorite.olx_id == olx_id)
        )
        result = await self.session.execute(query)
        favorite = result.scalars().first()
        if favorite:
            await self.session.delete(favorite)
            await self.session.flush()
            return True
        return False

    async def get_all(self, user_id: int) -> list[Favorite]:
        query = select(Favorite).where(Favorite.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
