from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.connection_key import ConnectionKey
from app.services.auth import decode_jwt


def get_current_user(
    authorization: str = Header(..., description="Bearer <jwt_token> or Bearer <connection_key>"),
    db: Session = Depends(get_db),
) -> User:
    """
    Unified auth dependency. Looks at the Authorization header and figures out
    whether this is a dashboard user (JWT) or an agent (connection key).

    - If the token starts with "argus_ck_" → look it up in connection_keys table,
      then resolve profile → user
    - Otherwise → decode it as a JWT token

    Returns the User object in both cases.
    Raises 401 if invalid.
    """
    # Strip "Bearer " prefix
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must start with 'Bearer '")

    token = authorization[len("Bearer "):]

    if token.startswith("argus_ak_"):
        # Connection key auth (agent)
        return _auth_connection_key(token, db)
    else:
        # JWT auth
        return _auth_jwt(token, db)


def _auth_connection_key(key_value: str, db: Session) -> User:
    """Authenticate using a connection key. Resolves key → profile → user."""
    now = datetime.now(timezone.utc)

    connection_key = db.query(ConnectionKey).filter(
        ConnectionKey.key_value == key_value,
        ConnectionKey.is_active == True,
    ).first()

    if not connection_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_AGENT_KEY", "message": "Connection key is invalid or revoked"},
        )

    # Check optional expiry
    if connection_key.expiry and connection_key.expiry < now:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_AGENT_KEY", "message": "Connection key has expired"},
        )

    # Resolve user through profile
    profile = db.query(Profile).filter(Profile.id == connection_key.profile_id).first()
    if not profile or not profile.is_active:
        raise HTTPException(status_code=401, detail="Profile is disabled or not found")

    user = db.query(User).filter(User.id == profile.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")

    return user


def _auth_jwt(token: str, db: Session) -> User:
    """Authenticate using a JWT token. Returns the User."""
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_TOKEN", "message": "JWT token is invalid or expired"},
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")

    return user
