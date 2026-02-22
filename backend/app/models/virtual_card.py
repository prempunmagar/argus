import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy import Numeric

from app.database import Base


class VirtualCard(Base):
    __tablename__ = "virtual_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), unique=True, nullable=False)  # One card per transaction
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    payment_method_id = Column(String, ForeignKey("payment_methods.id"), nullable=False)  # Which real card funds this

    # --- Card Details ---
    external_card_id = Column(String(255), nullable=True)       # Lithic card ID (null if mock)
    card_number = Column(String(19), nullable=False)             # Full number (encrypted in production)
    expiry_month = Column(String(2), nullable=False)             # "03"
    expiry_year = Column(String(4), nullable=False)              # "2026"
    cvv = Column(String(4), nullable=False)                      # "731"
    last_four = Column(String(4), nullable=False)                # "8847" for display

    # --- Limits ---
    spend_limit = Column(Numeric(10, 2), nullable=False)         # Max charge amount
    spend_limit_buffer = Column(Numeric(10, 2), nullable=False)  # Buffer above price (for tax/shipping)
    merchant_lock = Column(String(255), nullable=True)           # If set, card only works at this domain

    # --- Status ---
    status = Column(String(15), nullable=False, default="ACTIVE")  # ACTIVE, USED, EXPIRED, CANCELLED
    issued_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)                # 30 min from issuance
    used_at = Column(DateTime, nullable=True)                    # When charge was detected
    used_amount = Column(Numeric(10, 2), nullable=True)          # Actual charge amount
    cancelled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_virtual_cards_transaction_id", "transaction_id"),
        Index("idx_virtual_cards_status", "status"),
    )
