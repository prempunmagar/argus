import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.connection_key import ConnectionKey
from app.models.profile import Profile
from app.models.user import User
from app.schemas.connection_key import (
    ConnectionKeyCreatedResponse,
    ConnectionKeyItem,
    ConnectionKeysListResponse,
    CreateConnectionKeyRequest,
    RevokeKeyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _generate_key() -> tuple:
    """
    Generate a connection key value and display prefix.

    Uses secrets.token_hex(16) — 32 cryptographically random hex chars.
    Format: argus_ck_<32 hex chars>
    key_prefix: first 13 chars (e.g. "argus_ck_7f3b") — for display only.

    Auth at lookup time is a direct DB match on key_value (no rehashing needed).
    created_at on the ConnectionKey row is the canonical timestamp for this key.
    """
    key_value = "argus_ck_" + secrets.token_hex(16)
    key_prefix = key_value[:13]
    return key_value, key_prefix


# ── GET /connection-keys ───────────────────────────────────────────────────────

@router.get("/connection-keys", response_model=ConnectionKeysListResponse)
def list_connection_keys(
    profile_id: str = Query(..., description="Profile ID (required)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /connection-keys — List connection keys for a profile.
    Returns key_prefix only — full key_value is never exposed after creation.
    Auth: JWT.
    """
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    keys = db.query(ConnectionKey).filter(
        ConnectionKey.profile_id == profile_id,
    ).all()

    return ConnectionKeysListResponse(
        keys=[
            ConnectionKeyItem(
                id=k.id,
                key_prefix=k.key_prefix,
                label=k.label,
                is_active=k.is_active,
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
                created_at=k.created_at.isoformat(),
            )
            for k in keys
        ]
    )


# ── POST /connection-keys ──────────────────────────────────────────────────────

@router.post("/connection-keys", response_model=ConnectionKeyCreatedResponse, status_code=201)
def create_connection_key(
    body: CreateConnectionKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /connection-keys — Generate a new connection key for a profile.
    Full key_value is returned exactly once — it cannot be retrieved again.
    Auth: JWT.
    """
    profile = db.query(Profile).filter(
        Profile.id == body.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    key_value, key_prefix = _generate_key()

    ck = ConnectionKey(
        id=str(uuid.uuid4()),
        profile_id=body.profile_id,
        key_value=key_value,
        key_prefix=key_prefix,
        label=body.label,
        is_active=True,
    )
    db.add(ck)
    db.commit()
    db.refresh(ck)

    logger.info(f"Connection key created: id={ck.id} prefix={key_prefix} profile={body.profile_id}")

    return ConnectionKeyCreatedResponse(
        id=ck.id,
        key_value=key_value,
        key_prefix=key_prefix,
        label=ck.label,
        created_at=ck.created_at.isoformat(),
    )


# ── DELETE /connection-keys/{key_id} ──────────────────────────────────────────

@router.delete("/connection-keys/{key_id}", response_model=RevokeKeyResponse)
def revoke_connection_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    DELETE /connection-keys/{key_id} — Revoke a connection key (soft delete).
    Sets is_active=False. Agents using this key are immediately blocked.
    Auth: JWT.
    """
    ck = db.query(ConnectionKey).filter(ConnectionKey.id == key_id).first()
    if not ck:
        raise HTTPException(status_code=404, detail="Connection key not found")

    # Verify key's profile belongs to this user
    profile = db.query(Profile).filter(
        Profile.id == ck.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=403, detail="Not authorized")

    ck.is_active = False
    db.commit()

    return RevokeKeyResponse(
        id=ck.id,
        is_active=False,
        message="Key revoked. Any agents using this key will be immediately unable to make purchases.",
    )
