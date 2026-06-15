from database.engine import engine, AsyncSessionFactory
from database.models import Base


async def init_db():
    """Инициализация базы данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
