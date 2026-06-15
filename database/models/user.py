from sqlalchemy import BigInteger, String, Boolean, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), default="")
    
    # ACCESS CONTROL: новая система
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # Default False - блокировка
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    access_granted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Когда дан доступ
    access_denied_reason: Mapped[str] = mapped_column(String(256), default="")  # Причина блокировки

    # User filter preferences
    min_profit: Mapped[float] = mapped_column(Float, default=0.0)
    min_roi: Mapped[float] = mapped_column(Float, default=0.0)
    max_price: Mapped[float] = mapped_column(Float, default=999999.0)
    city_filter: Mapped[str | None] = mapped_column(String(128), nullable=True)
    keyword_blacklist: Mapped[str] = mapped_column(String(1024), default="")
    seller_blacklist: Mapped[str] = mapped_column(String(2048), default="")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    searches: Mapped[list["Search"]] = relationship("Search", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    ads_sent: Mapped[list["AdSent"]] = relationship("AdSent", back_populates="user", cascade="all, delete-orphan")
