from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database.models.search import Search
from typing import Optional


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, keyword: str, city_filter: str = None) -> Search:
        search = Search(user_id=user_id, keyword=keyword, city_filter=city_filter)
        self.session.add(search)
        await self.session.commit()
        await self.session.refresh(search)
        return search

    async def get_by_user(self, user_id: int) -> list[Search]:
        result = await self.session.execute(
            select(Search).where(Search.user_id == user_id, Search.is_active == True)
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> list[Search]:
        result = await self.session.execute(
            select(Search).where(Search.is_active == True)
        )
        return list(result.scalars().all())

    async def delete(self, search_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            delete(Search).where(Search.id == search_id, Search.user_id == user_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def exists(self, user_id: int, keyword: str) -> bool:
        result = await self.session.execute(
            select(Search).where(
                Search.user_id == user_id,
                Search.keyword == keyword,
                Search.is_active == True,
            )
        )
        return result.scalar_one_or_none() is not None
