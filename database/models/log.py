from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
