import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy import Numeric

from app.database import Base


class SpendingLedger(Base):
    __tablename__ = "spending_ledger"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("spending_categories.id"), nullable=False)
    period_type = Column(String(10), nullable=False)            # DAILY, WEEKLY, MONTHLY
    period_start = Column(Date, nullable=False)                  # Start date of the period
    total_spent = Column(Numeric(10, 2), nullable=False, default=0)  # Running total
    transaction_count = Column(Integer, nullable=False, default=0)
    last_updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "period_type", "period_start", name="uq_ledger_period"),
        Index("idx_ledger_lookup", "user_id", "category_id", "period_type", "period_start"),
    )
