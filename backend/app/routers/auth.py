from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.spending_category import SpendingCategory
from app.models.category_rule import CategoryRule
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    ErrorResponse,
)
from app.services.auth_service import hash_password, verify_password, create_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Side effects:
      - Creates the User row
      - Creates a default Profile ("Personal Shopper")
      - Creates a default "General" spending category (is_default=True) under that profile
      - Creates 3 default category rules for that General category:
          MAX_PER_TRANSACTION = 500.00
          AUTO_APPROVE_UNDER  = 50.00
          DAILY_LIMIT         = 1000.00
    """
    # 1. Check if email already taken
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"error": "EMAIL_EXISTS", "message": "An account with this email already exists"},
        )

    # 2. Create User
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    db.flush()  # flush so user.id is available for the FK references below

    # 3. Create default profile ("Personal Shopper")
    profile = Profile(
        user_id=user.id,
        name="Defualt",
        description="This is was created by defualt",
    )
    db.add(profile)
    db.flush()  # flush so profile.id is available for the FK below

    # 4. Create default "General" spending category under that profile
    general_category = SpendingCategory(
        profile_id=profile.id,
        name="General",
        description="Default for anything that doesn't fit other categories",
        is_default=True,
    )
    db.add(general_category)
    db.flush()  # flush so general_category.id is available for rules

    # 5. Create default rules for the General category
    default_rules = [
        CategoryRule(category_id=general_category.id, rule_type="MAX_PER_TRANSACTION", value="500.00"),
        CategoryRule(category_id=general_category.id, rule_type="AUTO_APPROVE_UNDER", value="50.00"),
        CategoryRule(category_id=general_category.id, rule_type="DAILY_LIMIT", value="1000.00"),
    ]
    db.add_all(default_rules)
    db.commit()
    db.refresh(user)

    # 6. Build response
    token = create_jwt(user.id, user.email)
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at.isoformat() + "Z",
        ),
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate an existing user and return a JWT token.
    """
    # 1. Find user by email
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    # 2. Verify password
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    # 3. Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    # 4. Build response
    token = create_jwt(user.id, user.email)
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at.isoformat() + "Z",
        ),
        token=token,
    )
