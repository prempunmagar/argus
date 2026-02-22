import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Index

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), unique=True, nullable=False)
    category_id = Column(String, ForeignKey("spending_categories.id"), nullable=True)
    category_confidence = Column(Float, nullable=True)          # 0.0 - 1.0
    intent_match = Column(Float, nullable=True)                 # 0.0 - 1.0
    intent_summary = Column(Text, nullable=True)                # One-sentence summary from Gemini
    decision_reasoning = Column(Text, nullable=True)            # 2-3 sentence explanation from Gemini
    risk_flags = Column(Text, nullable=True, default="[]")      # JSON array of free-text risk descriptions
    rules_checked = Column(Text, nullable=True)                 # JSON array of rule check results
    decision = Column(String(20), nullable=False)               # APPROVE, DENY, HUMAN_NEEDED
    hedera_tx_id = Column(String(100), nullable=True)           # Hedera TX for EVALUATION_DECIDED event
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_evaluations_transaction_id", "transaction_id"),
    )
