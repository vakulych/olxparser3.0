from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    entry_type: Mapped[str] = mapped_column(String(16))  # "keyword" | "seller"
    value: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
