from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AiReport(Base):
    __tablename__ = "ai_reports"

    report_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    health_score: Mapped[str | None] = mapped_column(Text, nullable=True)
    tendency_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    report_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
