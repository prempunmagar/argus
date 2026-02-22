import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index

from app.database import Base


class HumanApproval(Base):
    __tablename__ = "human_approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), unique=True, nullable=False)
    evaluation_id = Column(String, ForeignKey("evaluations.id"), unique=True, nullable=False)
    requested_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime, nullable=True)              # When user clicked approve/deny (NULL if pending/timeout)
    value = Column(String(20), nullable=True)                   # APPROVE, DENY, TIMEOUT_DENY
    note = Column(Text, nullable=True)                          # Optional user note: "Too expensive, find cheaper"
    hedera_tx_id = Column(String(100), nullable=True)           # Hedera TX for HUMAN_APPROVAL_RESPONSE event

    __table_args__ = (
        Index("idx_human_approvals_evaluation_id", "evaluation_id"),
    )
