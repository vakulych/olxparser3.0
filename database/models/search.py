from sqlalchemy import BigInteger, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(256))
    city_filter: Mapped[str | None] = mapped_column(String(128), nullable=True)  # фильтр города per-search
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="searches")
