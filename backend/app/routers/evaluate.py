import json
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AgentContext, get_agent_context
from app.models.category_rule import CategoryRule
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.payment_method import PaymentMethod
from app.models.spending_category import SpendingCategory
from app.models.transaction import Transaction
from app.models.virtual_card import VirtualCard
from app.schemas.evaluate import (
    AIEvaluation,
    CategoryInfo,
    EvaluateRequest,
    EvaluateResponse,
    RuleResult,
    VirtualCardResponse,
)
from app.services.card_issuer import issue_mock_card
from app.services.gemini_evaluator import call_gemini
from app.services.rules_engine import run_rules
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()

_HUMAN_APPROVAL_TIMEOUT = 300  # seconds


def _extract_domain(url: str) -> str:
    """Extract bare domain from a URL (strips www. prefix)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        return url


def _build_reason(decision: str, checks: list, category_name: str) -> str:
    """Build a human-readable reason string from the rules engine output."""
    if decision == "APPROVE":
        return f"All rules passed. Transaction auto-approved for {category_name}." if category_name else "All rules passed. Transaction auto-approved."
    # For DENY and HUMAN_NEEDED, use the first failing check's detail
    for check in checks:
        if not check.get("passed", True):
            return check.get("detail", "Transaction evaluated.")
    return "Transaction evaluated."


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    request: EvaluateRequest,
    agent_ctx: AgentContext = Depends(get_agent_context),
    db: Session = Depends(get_db),
):
    """
    POST /evaluate — The core 10-step evaluation pipeline.

    Auth: Connection key (argus_ck_...)
    Called by: ADK plugin / shopping agent
    """

    # ── Step 2: Extract merchant domain ────────────────────────────────────
    merchant_domain = _extract_domain(request.merchant_url)

    # ── Step 3: Create Transaction row ─────────────────────────────────────
    transaction = Transaction(
        user_id=agent_ctx.user_id,
        connection_key_id=agent_ctx.connection_key_id,
        status="PENDING_EVALUATION",
        request_data=json.dumps(request.model_dump()),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Broadcast TRANSACTION_CREATED
    await ws_manager.send_to_user(agent_ctx.user_id, {
        "type": "TRANSACTION_CREATED",
        "data": {
            "transaction_id": transaction.id,
            "product_name": request.product_name,
            "price": request.price,
            "merchant_name": request.merchant_name,
            "status": "PENDING_EVALUATION",
        },
    })

    # ── Step 4: Load profile's spending categories ──────────────────────────
    categories = db.query(SpendingCategory).filter(
        SpendingCategory.profile_id == agent_ctx.profile_id
    ).all()

    if not categories:
        raise HTTPException(status_code=500, detail="No spending categories configured for this profile")

    # Pre-load all active CUSTOM_RULE rules across all categories so Gemini
    # can evaluate them in one shot (avoids a second API call).
    all_custom_rules_for_gemini = []
    for cat in categories:
        custom_rules = db.query(CategoryRule).filter(
            CategoryRule.category_id == cat.id,
            CategoryRule.is_active == True,
            CategoryRule.rule_type == "CUSTOM_RULE",
        ).all()
        for rule in custom_rules:
            all_custom_rules_for_gemini.append({"id": rule.id, "prompt": rule.value})

    # ── Step 5: Call Gemini ─────────────────────────────────────────────────
    categories_for_gemini = [
        {
            "name": cat.name,
            "description": cat.description or "",
            "keywords": json.loads(cat.keywords or "[]"),
            "is_default": cat.is_default,
        }
        for cat in categories
    ]

    gemini_result = call_gemini(
        categories=categories_for_gemini,
        product_name=request.product_name,
        price=request.price,
        currency=request.currency,
        merchant_name=request.merchant_name,
        merchant_url=request.merchant_url,
        conversation_context=request.conversation_context,
        custom_rules=all_custom_rules_for_gemini,
    )

    # ── Step 6: Match category from Gemini response ─────────────────────────
    category_name_from_gemini = gemini_result.get("category_name", "")
    matched_category = next(
        (c for c in categories if c.name == category_name_from_gemini), None
    )
    if not matched_category:
        matched_category = next((c for c in categories if c.is_default), None)
    if not matched_category:
        matched_category = categories[0]

    # ── Step 6b: Create Evaluation row ─────────────────────────────────────
    evaluation = Evaluation(
        transaction_id=transaction.id,
        category_id=matched_category.id,
        category_confidence=gemini_result.get("category_confidence"),
        intent_match=gemini_result.get("intent_match"),
        intent_summary=gemini_result.get("intent_summary"),
        decision_reasoning=gemini_result.get("reasoning"),
        risk_flags=json.dumps(gemini_result.get("risk_flags", [])),
        rules_checked="[]",
        decision="PENDING",  # updated after rules engine
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # ── Step 7: Load rules for matched category ─────────────────────────────
    rules = db.query(CategoryRule).filter(
        CategoryRule.category_id == matched_category.id,
        CategoryRule.is_active == True,
    ).all()

    # ── Step 8: Run deterministic rules engine ──────────────────────────────
    checks, decision = run_rules(
        db=db,
        rules=rules,
        category_id=matched_category.id,
        price=request.price,
        merchant_domain=merchant_domain,
        gemini_result=gemini_result,
    )

    # ── Step 9: Update evaluation with decision ─────────────────────────────
    evaluation.rules_checked = json.dumps(checks)
    evaluation.decision = decision
    db.commit()

    # ── Step 10: Execute decision ───────────────────────────────────────────
    reason = _build_reason(decision, checks, matched_category.name)
    virtual_card_response = None
    timeout_seconds = None

    if decision == "APPROVE":
        transaction.status = "AI_APPROVED"
        db.commit()

        # Resolve payment method: category-specific → user default → any active
        payment_method_id = matched_category.payment_method_id
        if not payment_method_id:
            default_pm = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == agent_ctx.user_id,
                PaymentMethod.is_default == True,
                PaymentMethod.status == "active",
            ).first()
            if default_pm:
                payment_method_id = default_pm.id
        if not payment_method_id:
            any_pm = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == agent_ctx.user_id,
                PaymentMethod.status == "active",
            ).first()
            if any_pm:
                payment_method_id = any_pm.id
        if not payment_method_id:
            payment_method_id = "none"  # no payment method configured

        # Issue mock virtual card
        card_data = issue_mock_card(transaction.id, request.price, merchant_domain)

        # Persist VirtualCard row
        virtual_card = VirtualCard(
            transaction_id=transaction.id,
            user_id=agent_ctx.user_id,
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
        db.commit()

        virtual_card_response = VirtualCardResponse(
            card_number=card_data["card_number"],
            expiry_month=card_data["expiry_month"],
            expiry_year=card_data["expiry_year"],
            cvv=card_data["cvv"],
            last_four=card_data["last_four"],
            spend_limit=card_data["spend_limit"],
            merchant_lock=card_data["merchant_lock"],
            expires_at=card_data["expires_at_iso"],
        )

        await ws_manager.send_to_user(agent_ctx.user_id, {
            "type": "TRANSACTION_DECIDED",
            "data": {
                "transaction_id": transaction.id,
                "decision": "APPROVE",
                "reason": reason,
                "category_name": matched_category.name,
                "virtual_card_last_four": card_data["last_four"],
            },
        })

    elif decision == "DENY":
        transaction.status = "AI_DENIED"
        db.commit()

        await ws_manager.send_to_user(agent_ctx.user_id, {
            "type": "TRANSACTION_DECIDED",
            "data": {
                "transaction_id": transaction.id,
                "decision": "DENY",
                "reason": reason,
                "category_name": matched_category.name,
                "virtual_card_last_four": None,
            },
        })

    elif decision == "HUMAN_NEEDED":
        timeout_seconds = _HUMAN_APPROVAL_TIMEOUT
        transaction.status = "HUMAN_NEEDED"
        db.commit()

        human_approval = HumanApproval(
            transaction_id=transaction.id,
            evaluation_id=evaluation.id,
        )
        db.add(human_approval)
        db.commit()

        await ws_manager.send_to_user(agent_ctx.user_id, {
            "type": "APPROVAL_REQUIRED",
            "data": {
                "transaction_id": transaction.id,
                "product_name": request.product_name,
                "price": request.price,
                "merchant_name": request.merchant_name,
                "category_name": matched_category.name,
                "reason": reason,
                "timeout_seconds": timeout_seconds,
            },
        })

    # ── Build response ──────────────────────────────────────────────────────
    category_info = CategoryInfo(
        id=matched_category.id,
        name=matched_category.name,
        confidence=gemini_result.get("category_confidence", 0.5),
    )

    rules_applied = [RuleResult(**check) for check in checks]

    ai_eval = AIEvaluation(
        category_name=gemini_result.get("category_name"),
        category_confidence=gemini_result.get("category_confidence"),
        intent_match=gemini_result.get("intent_match"),
        intent_summary=gemini_result.get("intent_summary"),
        risk_flags=gemini_result.get("risk_flags", []),
        reasoning=gemini_result.get("reasoning"),
    )

    logger.info(
        f"Evaluate: txn={transaction.id} decision={decision} "
        f"category={matched_category.name} price={request.price}"
    )

    return EvaluateResponse(
        transaction_id=transaction.id,
        decision=decision,
        reason=reason,
        category=category_info,
        rules_applied=rules_applied,
        ai_evaluation=ai_eval,
        virtual_card=virtual_card_response,
        timeout_seconds=timeout_seconds,
    )
