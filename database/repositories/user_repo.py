from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models.user import User
from typing import Optional


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, username: str = None, full_name: str = "") -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id, username=username, full_name=full_name)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def get(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_all_active(self) -> list[User]:
        result = await self.session.execute(select(User).where(User.is_active == True))
        return list(result.scalars().all())

    async def update_settings(self, user_id: int, **kwargs) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self.session.commit()
