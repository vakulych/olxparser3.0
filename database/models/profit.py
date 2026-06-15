from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class Profit(Base):
    __tablename__ = "profits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    olx_id: Mapped[str] = mapped_column(String(64), index=True)
    purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    sale_price: Mapped[float] = mapped_column(Float, default=0.0)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
