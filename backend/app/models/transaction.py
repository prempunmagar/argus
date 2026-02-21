import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    connection_key_id = Column(String, ForeignKey("connection_keys.id"), nullable=False)
    status = Column(String(25), nullable=False, default="PENDING_EVALUATION")
    request_data = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_created_at", "created_at"),
    )
