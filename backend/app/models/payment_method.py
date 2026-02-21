import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index

from app.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    label = Column(String(100), nullable=False)          # "Visa ending 4242"
    type = Column(String(20), nullable=False)             # CREDIT_CARD, DEBIT_CARD, BANK_ACCOUNT
    last_four = Column(String(4), nullable=False)         # "4242"
    provider = Column(String(20), nullable=False)         # visa, mastercard, amex, discover
    funding_source_id = Column(String(255), nullable=True)  # Lithic reference or mock
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_payment_methods_user_id", "user_id"),
    )
