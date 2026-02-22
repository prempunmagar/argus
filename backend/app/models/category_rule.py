import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index

from app.database import Base


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("spending_categories.id"), nullable=False)
    rule_type = Column(String(30), nullable=False)   # MAX_PER_TRANSACTION, DAILY_LIMIT, MERCHANT_WHITELIST, etc.
    value = Column(Text, nullable=False)              # "150.00" or '["amazon.com","target.com"]' or "true"
    currency = Column(String(3), nullable=True, default="USD")  # Only for monetary rules
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    # NOTE: No updated_at — rules are immutable. To change a rule, deactivate the old row
    # (is_active=False) and create a new one. This gives a full audit trail.

    __table_args__ = (
        Index("idx_category_rules_category_id", "category_id"),
    )
