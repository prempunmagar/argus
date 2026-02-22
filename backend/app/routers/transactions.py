import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_agent_context, AgentContext
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.spending_category import SpendingCategory
from app.models.transaction import Transaction
from app.models.virtual_card import VirtualCard
from app.models.profile import Profile
from app.models.user import User
from app.schemas.transaction import (
    TransactionDetail,
    TransactionEvaluationDetail,
    TransactionEvaluationSummary,
    TransactionListItem,
    TransactionListResponse,
    TransactionRequestData,
    TransactionStatusResponse,
    VirtualCardDetail,
)

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
    """Parse request_data JSON blob into schema."""
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
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
    agent_ctx: AgentContext = Depends(get_agent_context),
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
