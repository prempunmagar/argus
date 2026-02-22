import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.payment_method import PaymentMethod
from app.models.spending_category import SpendingCategory
from app.models.transaction import Transaction
from app.models.virtual_card import VirtualCard
from app.models.user import User
from app.schemas.approval import ApproveRequest, DenyRequest
from app.services.card_issuer import issue_mock_card
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /transactions/{id}/approve ───────────────────────────────────────────

@router.post("/transactions/{transaction_id}/approve", status_code=204)
async def approve_transaction(
    transaction_id: str,
    body: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /transactions/{id}/approve — Dashboard user approves a pending transaction.

    Side effects:
    - Issues a virtual card (stored in virtual_cards table)
    - Updates HumanApproval row: value=APPROVE, responded_at=now
    - Updates Transaction: status=HUMAN_APPROVED
    - Broadcasts TRANSACTION_DECIDED via WebSocket

    Response: 204 No Content.
    The virtual card is retrieved by the shopping agent via GET /transactions/{id}/status.
    Auth: JWT.
    """
    # Load and validate transaction
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.status != "HUMAN_NEEDED":
        raise HTTPException(
            status_code=409,
            detail=f"Transaction cannot be approved — current status is '{txn.status}'"
        )

    # Load evaluation (needed for category → payment method + category name for WS)
    evaluation = db.query(Evaluation).filter(
        Evaluation.transaction_id == transaction_id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=500, detail="Evaluation record missing")

    # Load category for payment method + WS message
    category = None
    if evaluation.category_id:
        category = db.query(SpendingCategory).filter(
            SpendingCategory.id == evaluation.category_id
        ).first()

    # Parse price + merchant_domain from request_data blob
    try:
        request_data = json.loads(txn.request_data)
    except Exception:
        request_data = {}
    price = float(request_data.get("price", 0))
    merchant_domain = request_data.get("merchant_domain", "")

    # Resolve payment method: category preferred → user default → any active
    payment_method_id = category.payment_method_id if category else None
    if not payment_method_id:
        default_pm = db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == True,
            PaymentMethod.status == "active",
        ).first()
        if default_pm:
            payment_method_id = default_pm.id
    if not payment_method_id:
        any_pm = db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.status == "active",
        ).first()
        if any_pm:
            payment_method_id = any_pm.id
    if not payment_method_id:
        payment_method_id = "none"

    # Issue mock virtual card
    card_data = issue_mock_card(transaction_id, price, merchant_domain)

    # Persist VirtualCard row
    virtual_card = VirtualCard(
        transaction_id=transaction_id,
        user_id=current_user.id,
        payment_method_id=payment_method_id,
        external_card_id=card_data["external_card_id"],
        card_number=card_data["card_number"],
        expiry_month=card_data["expiry_month"],
        expiry_year=card_data["expiry_year"],
        cvv=card_data["cvv"],
        last_four=card_data["last_four"],
        spend_limit=card_data["spend_limit"],
        spend_limit_buffer=card_data["spend_limit_buffer"],
        merchant_lock=card_data["merchant_lock"],
        status="ACTIVE",
        issued_at=card_data["issued_at"],
        expires_at=card_data["expires_at"],
    )
    db.add(virtual_card)

    # Update HumanApproval row
    approval = db.query(HumanApproval).filter(
        HumanApproval.transaction_id == transaction_id
    ).first()
    if approval:
        approval.value = "APPROVE"
        approval.responded_at = datetime.now(timezone.utc)
        approval.note = body.note

    # Update Transaction status
    txn.status = "HUMAN_APPROVED"
    txn.updated_at = datetime.now(timezone.utc)

    db.commit()

    # Broadcast TRANSACTION_DECIDED
    category_name = category.name if category else "Unknown"
    await ws_manager.send_to_user(current_user.id, {
        "type": "TRANSACTION_DECIDED",
        "data": {
            "transaction_id": transaction_id,
            "decision": "APPROVE",
            "reason": f"Approved by user. {body.note or ''}".strip(),
            "category_name": category_name,
            "virtual_card_last_four": card_data["last_four"],
        },
    })

    logger.info(f"Approve: txn={transaction_id} user={current_user.id} card_last_four={card_data['last_four']}")
    return Response(status_code=204)


# ── POST /transactions/{id}/deny ──────────────────────────────────────────────

@router.post("/transactions/{transaction_id}/deny", status_code=204)
async def deny_transaction(
    transaction_id: str,
    body: DenyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /transactions/{id}/deny — Dashboard user denies a pending transaction.

    Side effects:
    - Updates HumanApproval row: value=DENY, responded_at=now
    - Updates Transaction: status=HUMAN_DENIED
    - Broadcasts TRANSACTION_DECIDED via WebSocket

    Response: 204 No Content.
    Auth: JWT.
    """
    # Load and validate transaction
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn.status != "HUMAN_NEEDED":
        raise HTTPException(
            status_code=409,
            detail=f"Transaction cannot be denied — current status is '{txn.status}'"
        )

    # Load category name for WS message
    evaluation = db.query(Evaluation).filter(
        Evaluation.transaction_id == transaction_id
    ).first()
    category_name = "Unknown"
    if evaluation and evaluation.category_id:
        category = db.query(SpendingCategory).filter(
            SpendingCategory.id == evaluation.category_id
        ).first()
        if category:
            category_name = category.name

    # Update HumanApproval row
    approval = db.query(HumanApproval).filter(
        HumanApproval.transaction_id == transaction_id
    ).first()
    if approval:
        approval.value = "DENY"
        approval.responded_at = datetime.now(timezone.utc)
        approval.note = body.note

    # Update Transaction status
    txn.status = "HUMAN_DENIED"
    txn.updated_at = datetime.now(timezone.utc)

    db.commit()

    # Build denial reason for WS
    reason = f"Denied by user. {body.note or ''}".strip()

    # Broadcast TRANSACTION_DECIDED
    await ws_manager.send_to_user(current_user.id, {
        "type": "TRANSACTION_DECIDED",
        "data": {
            "transaction_id": transaction_id,
            "decision": "DENY",
            "reason": reason,
            "category_name": category_name,
            "virtual_card_last_four": None,
        },
    })

    logger.info(f"Deny: txn={transaction_id} user={current_user.id} note={body.note!r}")
    return Response(status_code=204)
