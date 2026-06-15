from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.search import Search
from datetime import datetime


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, keyword: str, city_filter: str = None) -> Search:
        search = Search(user_id=user_id, keyword=keyword, city_filter=city_filter, is_active=True)
        self.session.add(search)
        await self.session.flush()
        return search

    async def get_all_active() -> list[Search]:
        query = select(Search).where(Search.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_user(self, user_id: int) -> list[Search]:
        query = select(Search).where(and_(Search.user_id == user_id, Search.is_active == True))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete(self, search_id: int) -> bool:
        search = await self.session.get(Search, search_id)
        if search:
            search.is_active = False
            await self.session.flush()
            return True
        return False
