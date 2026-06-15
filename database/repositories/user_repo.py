from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import User
from datetime import datetime


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, username: str = None, full_name: str = "") -> User:
        """Получить или создать пользователя. При создании доступ БЛОКИРОВАН."""
        user = await self.get(user_id)
        if user:
            return user

        user = User(
            id=user_id,
            username=username,
            full_name=full_name,
            is_active=False,  # ⭐ Новые пользователи по умолчанию БЕЗ доступа
            access_denied_reason="Ожидание активации администратором"
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get(self, user_id: int) -> User | None:
        """Получить пользователя по ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def grant_access(self, user_id: int) -> User | None:
        """Дать доступ пользователю."""
        user = await self.get(user_id)
        if user:
            user.is_active = True
            user.access_granted_at = datetime.utcnow()
            user.access_denied_reason = ""
            await self.session.flush()
        return user

    async def revoke_access(self, user_id: int, reason: str = "Доступ отозван администратором") -> User | None:
        """Отозвать доступ пользователя."""
        user = await self.get(user_id)
        if user:
            user.is_active = False
            user.access_denied_reason = reason
            await self.session.flush()
        return user

    async def get_all_users() -> list[User]:
        """Получить всех пользователей (для админа)."""
        query = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, user_id: int, **kwargs) -> User | None:
        """Обновить данные пользователя."""
        user = await self.get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.session.flush()
        return user
