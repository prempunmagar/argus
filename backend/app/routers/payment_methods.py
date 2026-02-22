import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.schemas.payment_method import (
    CreatePaymentMethodRequest,
    PaymentMethodResponse,
    PaymentMethodsListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helper ─────────────────────────────────────────────────────────────────────

def _pm_to_response(pm: PaymentMethod) -> PaymentMethodResponse:
    try:
        detail = json.loads(pm.detail) if isinstance(pm.detail, str) else pm.detail
    except Exception:
        detail = {}
    return PaymentMethodResponse(
        id=pm.id,
        nickname=pm.nickname,
        method_type=pm.method_type,
        status=pm.status,
        is_default=pm.is_default,
        detail=detail,
    )


# ── GET /payment-methods ───────────────────────────────────────────────────────

@router.get("/payment-methods", response_model=PaymentMethodsListResponse)
def list_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /payment-methods — List all payment methods for the authenticated user.
    Account-level (not profile-scoped).
    Auth: JWT.
    """
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
    ).all()

    return PaymentMethodsListResponse(
        payment_methods=[_pm_to_response(pm) for pm in methods]
    )


# ── POST /payment-methods ──────────────────────────────────────────────────────

@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=201)
def create_payment_method(
    body: CreatePaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /payment-methods — Add a new payment method.
    If is_default=True, all existing defaults for this user are unset first.
    Auth: JWT.
    """
    # If this will be the new default, unset existing ones first
    if body.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == True,
        ).update({"is_default": False})

    pm = PaymentMethod(
        user_id=current_user.id,
        method_type=body.method_type,
        nickname=body.nickname,
        detail=json.dumps(body.detail) if isinstance(body.detail, dict) else body.detail,
        is_default=body.is_default,
        status="active",
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)

    logger.info(f"Payment method created: id={pm.id} type={pm.method_type} user={current_user.id}")
    return _pm_to_response(pm)
