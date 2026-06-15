from sqlalchemy import String, Float, Integer, Text, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    olx_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="UAH")
    url: Mapped[str] = mapped_column(String(1024))
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Seller info
    seller_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller_created: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller_ads_count: Mapped[int] = mapped_column(Integer, default=0)

    # Analytics
    market_price: Mapped[float] = mapped_column(Float, default=0.0)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    roi: Mapped[float] = mapped_column(Float, default=0.0)
    flip_score: Mapped[int] = mapped_column(Integer, default=0)
    seller_status: Mapped[str] = mapped_column(String(32), default="unknown")

    keyword: Mapped[str] = mapped_column(String(256), default="")
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
