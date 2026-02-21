import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index

from app.database import Base


class SpendingCategory(Base):
    __tablename__ = "spending_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)              # "Footwear", "Electronics", "Travel"
    description = Column(Text, nullable=True)                # Helps Gemini categorize
    keywords = Column(Text, nullable=True, default="[]")     # JSON array: ["shoes", "sneakers"]
    payment_method_id = Column(String, ForeignKey("payment_methods.id"), nullable=True)  # Preferred card for this category
    is_default = Column(Boolean, nullable=False, default=False)  # Fallback category — one per user
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_spending_categories_user_id", "user_id"),
    )
