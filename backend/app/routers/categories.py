import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category_rule import CategoryRule
from app.models.evaluation import Evaluation
from app.models.payment_method import PaymentMethod
from app.models.profile import Profile
from app.models.spending_category import SpendingCategory
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.category import (
    CategoriesListResponse,
    CategoryResponse,
    CategoryRuleItem,
    CreateCategoryRequest,
    PaymentMethodSummary,
    UpdateCategoryRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_APPROVED_STATUSES = ["AI_APPROVED", "HUMAN_APPROVED", "COMPLETED"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_spending_total(db: Session, category_id: str, since: datetime) -> float:
    """
    Sum the price of all approved transactions for a category since `since`.
    Joins Transaction → Evaluation, filters on Transaction.status and category_id.
    """
    rows = (
        db.query(Transaction)
        .join(Evaluation, Evaluation.transaction_id == Transaction.id)
        .filter(
            Evaluation.category_id == category_id,
            Transaction.status.in_(_APPROVED_STATUSES),
            Transaction.created_at >= since,
        )
        .all()
    )
    total = 0.0
    for txn in rows:
        try:
            data = json.loads(txn.request_data)
            total += float(data.get("price", 0))
        except Exception:
            pass
    return round(total, 2)


def _build_category_response(db: Session, cat: SpendingCategory) -> CategoryResponse:
    """Build a full CategoryResponse for a SpendingCategory ORM object."""
    now = datetime.now(timezone.utc)

    # Payment method summary (optional)
    pm_summary = None
    if cat.payment_method_id:
        pm = db.query(PaymentMethod).filter(
            PaymentMethod.id == cat.payment_method_id
        ).first()
        if pm:
            pm_summary = PaymentMethodSummary(
                id=pm.id,
                nickname=pm.nickname,
                method_type=pm.method_type,
            )

    # Active rules only
    rules = db.query(CategoryRule).filter(
        CategoryRule.category_id == cat.id,
        CategoryRule.is_active == True,
    ).all()

    rule_items = [
        CategoryRuleItem(
            id=r.id,
            rule_type=r.rule_type,
            value=r.value,
            is_active=r.is_active,
        )
        for r in rules
    ]

    # Spending totals
    spending_today = _get_spending_total(db, cat.id, now - timedelta(days=1))
    spending_this_week = _get_spending_total(db, cat.id, now - timedelta(weeks=1))
    spending_this_month = _get_spending_total(db, cat.id, now - timedelta(days=30))

    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        is_default=cat.is_default,
        payment_method=pm_summary,
        rules=rule_items,
        spending_today=spending_today,
        spending_this_week=spending_this_week,
        spending_this_month=spending_this_month,
    )


# ── GET /categories ────────────────────────────────────────────────────────────

@router.get("/categories", response_model=CategoriesListResponse)
def list_categories(
    profile_id: str = Query(..., description="Profile ID (required)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /categories — List all spending categories for a profile.
    Includes nested active rules and spending totals (today/week/month).
    Auth: JWT.
    """
    # Verify profile belongs to this user
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    categories = db.query(SpendingCategory).filter(
        SpendingCategory.profile_id == profile_id
    ).all()

    return CategoriesListResponse(
        categories=[_build_category_response(db, cat) for cat in categories]
    )


# ── POST /categories ───────────────────────────────────────────────────────────

@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CreateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /categories — Create a new spending category with rules.
    Auth: JWT.
    """
    # Verify profile belongs to this user
    profile = db.query(Profile).filter(
        Profile.id == body.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create the category row
    cat = SpendingCategory(
        profile_id=body.profile_id,
        name=body.name,
        description=body.description,
        payment_method_id=body.payment_method_id,
        is_default=False,  # New categories via API are never default
    )
    db.add(cat)
    db.flush()  # Populate cat.id before creating rules

    # Create rule rows
    for rule_data in body.rules:
        rule = CategoryRule(
            category_id=cat.id,
            rule_type=rule_data.rule_type,
            value=rule_data.value,
            is_active=True,
        )
        db.add(rule)

    db.commit()
    db.refresh(cat)
    return _build_category_response(db, cat)


# ── PUT /categories/{id} ───────────────────────────────────────────────────────

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    body: UpdateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PUT /categories/{id} — Partial update for a spending category.
    Only provided fields are updated.
    If `rules` is provided, old active rules are deactivated and new rows created
    (immutable audit-trail design per spec Section 2.5).
    Auth: JWT.
    """
    # Look up category
    cat = db.query(SpendingCategory).filter(
        SpendingCategory.id == category_id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verify category's profile belongs to this user
    profile = db.query(Profile).filter(
        Profile.id == cat.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Apply partial updates to category fields
    if body.name is not None:
        cat.name = body.name
    if body.description is not None:
        cat.description = body.description
    if body.payment_method_id is not None:
        cat.payment_method_id = body.payment_method_id
    cat.updated_at = datetime.now(timezone.utc)

    # Handle rules update (immutable design: deactivate old, insert new)
    if body.rules is not None:
        # Deactivate all currently active rules for this category
        active_rules = db.query(CategoryRule).filter(
            CategoryRule.category_id == category_id,
            CategoryRule.is_active == True,
        ).all()
        for rule in active_rules:
            rule.is_active = False

        # Insert new rule rows
        for rule_data in body.rules:
            new_rule = CategoryRule(
                category_id=category_id,
                rule_type=rule_data.rule_type,
                value=rule_data.value,
                is_active=True,
            )
            db.add(new_rule)

    db.commit()
    db.refresh(cat)
    return _build_category_response(db, cat)
