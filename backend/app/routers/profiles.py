from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category_rule import CategoryRule
from app.models.profile import Profile
from app.models.spending_category import SpendingCategory
from app.models.user import User
from app.schemas.profile import (
    CreateProfileRequest,
    ProfileResponse,
    ProfilesListResponse,
    UpdateProfileRequest,
)

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

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
