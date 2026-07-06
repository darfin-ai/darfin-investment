from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserTradingStats(Base):
    __tablename__ = "user_trading_stats"

    stat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    monthly_trade_freq: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_hold_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    chase_buy_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
