from sqlalchemy import BigInteger, String, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class Profit(Base):
    __tablename__ = "profits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    olx_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    buy_price: Mapped[float] = mapped_column(Float, default=0.0)
    sell_price: Mapped[float] = mapped_column(Float, default=0.0)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="found")  # found | bought | sold
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    sold_at: Mapped[datetime | None] = mapped_column(nullable=True)
