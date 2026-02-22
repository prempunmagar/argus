import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_connection_key_context, AgentContext
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.payment_method import PaymentMethod
from app.models.spending_category import SpendingCategory
from app.models.transaction import Transaction
from app.models.virtual_card import VirtualCard
from app.models.profile import Profile
from app.models.user import User
from app.schemas.transaction import (
    RespondRequest,
    RespondResponse,
    TransactionDetail,
    TransactionEvaluationDetail,
    TransactionEvaluationSummary,
    TransactionListItem,
    TransactionListResponse,
    TransactionRequestData,
    TransactionStatusResponse,
    VirtualCardDetail,
)
from app.services.card_issuer import issue_mock_card
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()

_HUMAN_APPROVAL_TIMEOUT = 300  # seconds


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        return url


def _parse_request_data(raw: str) -> TransactionRequestData:
    """Parse request_data JSON blob into schema.

    Supports both v2 nested format {product: {...}, chat_history: "..."}
    and v1 flat format {product_name, price, merchant_url, ...}.
    """
    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    # v2 nested format: {product: {product_name, price, ...}, chat_history}
    if "product" in data and isinstance(data["product"], dict):
        p = data["product"]
        merchant_url = p.get("merchant_url", "")
        return TransactionRequestData(
            product_name=p.get("product_name", "Unknown"),
            price=float(p.get("price", 0)),
            currency=p.get("currency", "USD"),
            merchant_name=p.get("merchant_name", "Unknown"),
            merchant_url=merchant_url,
            merchant_domain=_extract_domain(merchant_url) if merchant_url else None,
            product_url=p.get("product_url"),
            conversation_context=data.get("chat_history"),
        )

    # v1 flat format fallback
    merchant_url = data.get("merchant_url", "")
    return TransactionRequestData(
        product_name=data.get("product_name", "Unknown"),
        price=float(data.get("price", 0)),
        currency=data.get("currency", "USD"),
        merchant_name=data.get("merchant_name", "Unknown"),
        merchant_url=merchant_url,
        merchant_domain=_extract_domain(merchant_url) if merchant_url else None,
        product_url=data.get("product_url"),
        conversation_context=data.get("conversation_context"),
    )


def _build_virtual_card_detail(vc: VirtualCard) -> VirtualCardDetail:
    return VirtualCardDetail(
        card_number=vc.card_number,
        expiry_month=vc.expiry_month,
        expiry_year=vc.expiry_year,
        cvv=vc.cvv,
        last_four=vc.last_four,
        spend_limit=float(vc.spend_limit),
        merchant_lock=vc.merchant_lock,
        expires_at=vc.expires_at.isoformat() if vc.expires_at else "",
        status=vc.status,
    )


# ── GET /transactions ─────────────────────────────────────────────────────────

@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(
    status: Optional[str] = Query(None, description="Filter by status"),
    category_id: Optional[str] = Query(None, description="Filter by category (via evaluation)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /transactions — List transactions for the authenticated user.
    Dashboard uses this for the transaction feed.
    """
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if status:
        query = query.filter(Transaction.status == status)

    if category_id:
        # Join to evaluations to filter by category
        query = (
            query.join(Evaluation, Evaluation.transaction_id == Transaction.id)
            .filter(Evaluation.category_id == category_id)
        )

    total = query.count()
    transactions = (
        query.order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Pre-load category names for this user's profiles
    profile_ids = [
        p.id for p in db.query(Profile).filter(Profile.user_id == current_user.id).all()
    ]
    categories = db.query(SpendingCategory).filter(
        SpendingCategory.profile_id.in_(profile_ids)
    ).all()
    category_map = {c.id: c.name for c in categories}

    items = []
    for txn in transactions:
        evaluation = db.query(Evaluation).filter(
            Evaluation.transaction_id == txn.id
        ).first()

        virtual_card = db.query(VirtualCard).filter(
            VirtualCard.transaction_id == txn.id
        ).first()

        eval_summary = None
        if evaluation:
            eval_summary = TransactionEvaluationSummary(
                decision=evaluation.decision,
                category_name=category_map.get(evaluation.category_id) if evaluation.category_id else None,
                category_confidence=evaluation.category_confidence,
                intent_match=evaluation.intent_match,
            )

        items.append(TransactionListItem(
            id=txn.id,
            status=txn.status,
            request_data=_parse_request_data(txn.request_data),
            evaluation=eval_summary,
            virtual_card_last_four=virtual_card.last_four if virtual_card else None,
            virtual_card_status=virtual_card.status if virtual_card else None,
            created_at=txn.created_at.isoformat(),
        ))

    return TransactionListResponse(
        transactions=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ── GET /transactions/{id} ────────────────────────────────────────────────────

@router.get("/transactions/{transaction_id}", response_model=TransactionDetail)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /transactions/{id} — Full transaction detail for the dashboard.
    """
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    evaluation = db.query(Evaluation).filter(
        Evaluation.transaction_id == txn.id
    ).first()

    virtual_card = db.query(VirtualCard).filter(
        VirtualCard.transaction_id == txn.id
    ).first()

    # Category name lookup
    category_name = None
    if evaluation and evaluation.category_id:
        cat = db.query(SpendingCategory).filter(
            SpendingCategory.id == evaluation.category_id
        ).first()
        category_name = cat.name if cat else None

    eval_detail = None
    if evaluation:
        try:
            risk_flags = json.loads(evaluation.risk_flags or "[]")
        except Exception:
            risk_flags = []
        try:
            rules_checked = json.loads(evaluation.rules_checked or "[]")
        except Exception:
            rules_checked = []

        eval_detail = TransactionEvaluationDetail(
            id=evaluation.id,
            decision=evaluation.decision,
            category_id=evaluation.category_id,
            category_name=category_name,
            category_confidence=evaluation.category_confidence,
            intent_match=evaluation.intent_match,
            intent_summary=evaluation.intent_summary,
            decision_reasoning=evaluation.decision_reasoning,
            risk_flags=risk_flags,
            rules_checked=rules_checked,
            created_at=evaluation.created_at.isoformat(),
        )

    vc_detail = _build_virtual_card_detail(virtual_card) if virtual_card else None

    return TransactionDetail(
        id=txn.id,
        status=txn.status,
        request_data=_parse_request_data(txn.request_data),
        evaluation=eval_detail,
        virtual_card=vc_detail,
        created_at=txn.created_at.isoformat(),
        updated_at=txn.updated_at.isoformat(),
    )


# ── GET /transactions/{id}/status (plugin polling) ────────────────────────────

@router.get("/transactions/{transaction_id}/status", response_model=TransactionStatusResponse)
def get_transaction_status(
    transaction_id: str,
    agent_ctx: AgentContext = Depends(get_connection_key_context),
    db: Session = Depends(get_db),
):
    """
    GET /transactions/{id}/status — Plugin polls this while waiting for human approval.
    Auth: Connection key (agent only).
    Returns virtual card when HUMAN_APPROVED.
    """
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == agent_ctx.user_id,
    ).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    now = datetime.now(timezone.utc)
    waited_seconds = None
    virtual_card = None
    decision = None
    reason = None

    # Calculate waited_seconds from HumanApproval.requested_at
    if txn.status in ("HUMAN_NEEDED", "HUMAN_APPROVED", "HUMAN_DENIED", "HUMAN_TIMEOUT"):
        approval = db.query(HumanApproval).filter(
            HumanApproval.transaction_id == txn.id
        ).first()
        if approval:
            delta = now - approval.requested_at.replace(tzinfo=timezone.utc)
            waited_seconds = int(delta.total_seconds())

    # If approved, load virtual card and set decision
    if txn.status == "HUMAN_APPROVED":
        decision = "APPROVE"
        reason = "Approved by user"
        vc = db.query(VirtualCard).filter(
            VirtualCard.transaction_id == txn.id
        ).first()
        if vc:
            virtual_card = _build_virtual_card_detail(vc)

    elif txn.status == "HUMAN_DENIED":
        decision = "DENY"
        approval = db.query(HumanApproval).filter(
            HumanApproval.transaction_id == txn.id
        ).first()
        reason = f"Denied by user: {approval.note}" if (approval and approval.note) else "Denied by user"

    elif txn.status == "HUMAN_TIMEOUT":
        decision = "DENY"
        reason = "Approval timed out"

    return TransactionStatusResponse(
        transaction_id=txn.id,
        status=txn.status,
        decision=decision,
        reason=reason,
        virtual_card=virtual_card,
        waited_seconds=waited_seconds,
        timeout_seconds=_HUMAN_APPROVAL_TIMEOUT,
    )


# ── POST /transactions/{id}/respond ──────────────────────────────────────────

@router.post("/transactions/{transaction_id}/respond", response_model=RespondResponse)
async def respond_to_transaction(
    transaction_id: str,
    body: RespondRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /transactions/{id}/respond — Dashboard user approves or denies a pending transaction.

    Request body: {action: "APPROVE"|"DENY", note?: str}
    Returns 200 with body:
      - APPROVE → includes virtual_card details
      - DENY → includes reason

    Auth: JWT.
    """
    if body.action not in ("APPROVE", "DENY"):
        raise HTTPException(status_code=400, detail="action must be 'APPROVE' or 'DENY'")

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
            detail=f"Transaction cannot be responded to — current status is '{txn.status}'"
        )

    # Load evaluation (needed for category + WS message)
    evaluation = db.query(Evaluation).filter(
        Evaluation.transaction_id == transaction_id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=500, detail="Evaluation record missing")

    # Load category for WS message + payment method resolution
    category = None
    if evaluation.category_id:
        category = db.query(SpendingCategory).filter(
            SpendingCategory.id == evaluation.category_id
        ).first()
    category_name = category.name if category else "Unknown"

    # Update HumanApproval row
    approval = db.query(HumanApproval).filter(
        HumanApproval.transaction_id == transaction_id
    ).first()
    if approval:
        approval.value = body.action
        approval.responded_at = datetime.now(timezone.utc)
        approval.note = body.note

    virtual_card_detail = None

    if body.action == "APPROVE":
        # Parse price + merchant_domain from request_data blob (v2 nested or v1 flat)
        try:
            request_data = json.loads(txn.request_data)
        except Exception:
            request_data = {}
        if "product" in request_data and isinstance(request_data["product"], dict):
            p = request_data["product"]
            price = float(p.get("price", 0))
            merchant_url = p.get("merchant_url", "")
            merchant_domain = _extract_domain(merchant_url) if merchant_url else ""
        else:
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
        vc = VirtualCard(
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
        db.add(vc)

        # Update Transaction status
        txn.status = "HUMAN_APPROVED"
        txn.updated_at = datetime.now(timezone.utc)

        db.commit()

        virtual_card_detail = _build_virtual_card_detail(vc)
        reason = f"Approved by user. {body.note or ''}".strip()

        # Broadcast TRANSACTION_DECIDED
        await ws_manager.send_to_user(current_user.id, {
            "type": "TRANSACTION_DECIDED",
            "data": {
                "transaction_id": transaction_id,
                "decision": "APPROVE",
                "reason": reason,
                "category_name": category_name,
                "virtual_card_last_four": card_data["last_four"],
            },
        })

        logger.info(f"Respond APPROVE: txn={transaction_id} user={current_user.id} card_last_four={card_data['last_four']}")

    else:
        # DENY
        txn.status = "HUMAN_DENIED"
        txn.updated_at = datetime.now(timezone.utc)

        db.commit()

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

        logger.info(f"Respond DENY: txn={transaction_id} user={current_user.id} note={body.note!r}")

    return RespondResponse(
        transaction_id=transaction_id,
        action=body.action,
        reason=reason,
        virtual_card=virtual_card_detail,
    )
