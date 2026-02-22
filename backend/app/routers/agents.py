import logging
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category_rule import CategoryRule
from app.models.connection_key import ConnectionKey
from app.models.profile import Profile
from app.models.spending_category import SpendingCategory
from app.models.user import User
from app.schemas.agents import (
    ConnectionKeyCreatedResponse,
    ConnectionKeyItem,
    ConnectionKeysListResponse,
    CreateConnectionKeyRequest,
    CreateProfileRequest,
    ProfileResponse,
    ProfilesListResponse,
    RevokeKeyResponse,
    UpdateProfileRequest,
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


def _create_default_general_category(db: Session, profile_id: str) -> None:
    """
    Create a default General category + 3 default rules under a new profile.
    Same side effect as POST /auth/register.
    """
    general_cat = SpendingCategory(
        profile_id=profile_id,
        name="General",
        description="Default for anything that doesn't fit other categories",
        is_default=True,
    )
    db.add(general_cat)
    db.flush()

    db.add_all([
        CategoryRule(category_id=general_cat.id, rule_type="MAX_PER_TRANSACTION", value="500.00"),
        CategoryRule(category_id=general_cat.id, rule_type="AUTO_APPROVE_UNDER",  value="50.00"),
        CategoryRule(category_id=general_cat.id, rule_type="DAILY_LIMIT",         value="1000.00"),
    ])


def _profile_to_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        is_active=profile.is_active,
        created_at=profile.created_at.isoformat(),
    )


# ── GET /profiles ──────────────────────────────────────────────────────────────

@router.get("/profiles", response_model=ProfilesListResponse)
def list_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /profiles — List all active profiles for the authenticated user.
    Auth: JWT.
    """
    profiles = db.query(Profile).filter(
        Profile.user_id == current_user.id,
        Profile.is_active == True,
    ).all()

    return ProfilesListResponse(profiles=[_profile_to_response(p) for p in profiles])


# ── POST /profiles ─────────────────────────────────────────────────────────────

@router.post("/profiles", response_model=ProfileResponse, status_code=201)
def create_profile(
    body: CreateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /profiles — Create a new profile.
    Side effect: creates a default General category + 3 default rules.
    Auth: JWT.
    """
    profile = Profile(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    db.add(profile)
    db.flush()

    _create_default_general_category(db, profile.id)

    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


# ── PUT /profiles/{id} ─────────────────────────────────────────────────────────

@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: str,
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PUT /profiles/{id} — Partial update (name, description).
    Auth: JWT.
    """
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if body.name is not None:
        profile.name = body.name
    if body.description is not None:
        profile.description = body.description
    profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


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
