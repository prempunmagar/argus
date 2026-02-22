from pydantic import BaseModel
from typing import Optional, List


# ── Profile schemas ────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str


class ProfilesListResponse(BaseModel):
    profiles: List[ProfileResponse]


class CreateProfileRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ── Connection key schemas ─────────────────────────────────────────────────────

class ConnectionKeyItem(BaseModel):
    """Used in GET /connection-keys list — never exposes full key_value."""
    id: str
    key_prefix: str
    label: str
    is_active: bool
    last_used_at: Optional[str] = None
    created_at: str


class ConnectionKeysListResponse(BaseModel):
    keys: List[ConnectionKeyItem]


class CreateConnectionKeyRequest(BaseModel):
    profile_id: str
    label: str


class ConnectionKeyCreatedResponse(BaseModel):
    """Returned only on POST — full key_value shown exactly once."""
    id: str
    key_value: str    # Full key — save it now, it will not be shown again
    key_prefix: str
    label: str
    created_at: str
    warning: str = "Save this key now. It will not be shown again."


class RevokeKeyResponse(BaseModel):
    id: str
    is_active: bool
    message: str
