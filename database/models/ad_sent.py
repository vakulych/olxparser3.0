from sqlalchemy import String, Float, Integer, Text, BigInteger, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base


class AdSent(Base):
    """Таблица отправленных товаров для каждого пользователя.
    Это критично для фильтрации - каждый юзер видит только его товары.
    """
    __tablename__ = "ads_sent"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    olx_id: Mapped[str] = mapped_column(String(64), index=True)  # Не unique - один товар может быть отправлен многим

    # Основная информация о товаре
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="UAH")
    url: Mapped[str] = mapped_column(String(1024))
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Информация о продавце
    seller_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller_created: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Аналитика
    market_price: Mapped[float] = mapped_column(Float, default=0.0)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    roi: Mapped[float] = mapped_column(Float, default=0.0)
    flip_score: Mapped[int] = mapped_column(Integer, default=0)
    seller_status: Mapped[str] = mapped_column(String(32), default="unknown")

    # Поиск
    keyword: Mapped[str] = mapped_column(String(256), default="")
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Отношение
    user: Mapped["User"] = relationship("User", back_populates="ads_sent")
