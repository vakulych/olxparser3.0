from typing import Any
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import AsyncSessionFactory


class DbMiddleware(BaseMiddleware):
    """Middleware для передачи сессии БД в обработчики."""

    async def __call__(self, handler, event: Any, data: dict) -> Any:
        async with AsyncSessionFactory() as session:
            data["session"] = session
            return await handler(event, data)
