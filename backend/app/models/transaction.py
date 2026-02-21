import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy import Numeric

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    connection_key_id = Column(String, ForeignKey("connection_keys.id"), nullable=False)
    status = Column(String(25), nullable=False, default="PENDING_EVALUATION")

    # --- Request Data (what the agent sent us) ---
    product_name = Column(String(500), nullable=False)
    product_url = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)              # 89.99
    currency = Column(String(3), nullable=False, default="USD")
    merchant_name = Column(String(255), nullable=False)
    merchant_url = Column(Text, nullable=False)
    merchant_domain = Column(String(255), nullable=False)        # Extracted: "amazon.com"
    conversation_context = Column(Text, nullable=True)

    # --- Categorization (from Gemini) ---
    detected_category_id = Column(String, ForeignKey("spending_categories.id"), nullable=True)
    detected_category_name = Column(String(100), nullable=True)  # Denormalized for audit
    category_confidence = Column(Float, nullable=True)           # 0.0 - 1.0

    # --- Evaluation (rules + AI) ---
    rules_checked = Column(Text, nullable=True)      # JSON array of rule check results
    ai_evaluation = Column(Text, nullable=True)      # JSON object from Gemini
    decision = Column(String(20), nullable=True)     # APPROVE, DENY, REQUIRE_APPROVAL
    decision_reason = Column(Text, nullable=True)    # Human-readable explanation
    decided_at = Column(DateTime, nullable=True)

    # --- Human Approval ---
    approval_requested_at = Column(DateTime, nullable=True)
    approval_responded_at = Column(DateTime, nullable=True)
    approved_by = Column(String(20), nullable=True)  # AUTO, USER_APPROVE, USER_DENY, TIMEOUT_DENY

    # --- Virtual Card ---
    # No ForeignKey here because VirtualCard also references Transaction,
    # creating a circular dependency that SQLite can't handle.
    # We store the ID as a plain string and enforce the link in application code.
    virtual_card_id = Column(String, nullable=True)

    # --- Audit ---
    hedera_tx_id = Column(String(255), nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_created_at", "created_at"),
    )
