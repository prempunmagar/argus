import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index

from app.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    method_type = Column(String(20), nullable=False)             # CREDIT_CARD, DEBIT_CARD, BANK_ACCOUNT, CRYPTO_WALLET
    nickname = Column(String(100), nullable=False)               # "Work Visa Card"
    detail = Column(Text, nullable=False, default="{}")          # JSON: type-specific data (brand, last4, exp, etc.)
    is_default = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="active")  # active, inactive, expired, revoked, error
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_payment_methods_user_id", "user_id"),
    )
