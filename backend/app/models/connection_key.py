import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index

from app.database import Base


class ConnectionKey(Base):
    __tablename__ = "connection_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    key_value = Column(String(255), unique=True, nullable=False)   # Full key: argus_ck_ + 32 hex chars
    key_prefix = Column(String(20), nullable=False)                 # First 12 chars for display: "argus_ck_7f3b"
    label = Column(String(100), nullable=False)                     # "My Shopping Agent", "Dev Key"
    expires_at = Column(DateTime, nullable=True)                    # Optional: key invalid after this datetime
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_connection_keys_key_value", "key_value"),
        Index("idx_connection_keys_profile_id", "profile_id"),
    )
