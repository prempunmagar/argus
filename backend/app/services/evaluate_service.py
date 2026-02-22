"""
evaluate_service.py — Orchestrates the 5-phase /evaluate pipeline.

Phase 1: Validation + Setup      (steps 1-4)
Phase 2: AI Intent Extraction     (step 5 — Gemini Call 1)
Phase 3: Rules Engine             (steps 6-8)
Phase 4: AI Final Decision        (steps 9-10 — Gemini Call 2, only if not HARD_DENY)
Phase 5: Execute Decision         (steps 11-14)
"""

import asyncio
import json
import logging
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from app.services import hedera_service

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
from app.services.gemini_evaluator import extract_intent_and_category, make_final_decision
from app.services.rules_engine import evaluate_rules
from app.services.spending_service import get_spending_totals
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

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


def _build_reason(decision: str, checks: list, category_name: str, ai_reasoning: str = None) -> str:
    """Build a human-readable reason string."""
    if decision == "APPROVE":
        return f"All rules passed. Transaction auto-approved for {category_name}." if category_name else "All rules passed. Transaction auto-approved."
    if decision == "DENY":
        # Use the first failing check's detail
        for check in checks:
            if not check.get("passed", True):
                return check.get("detail", "Transaction denied.")
        return "Transaction denied."
    # HUMAN_NEEDED — use AI reasoning if available, else first failing check
    if ai_reasoning:
        return ai_reasoning
    for check in checks:
        if not check.get("passed", True):
            return check.get("detail", "Transaction requires human review.")
    return "Transaction requires human review."


async def run_evaluate_pipeline(
    request: EvaluateRequest,
    user_id: str,
    profile_id: str,
    connection_key_id: str,
    db: Session,
) -> EvaluateResponse:
    """
    The 14-step / 5-phase evaluation pipeline.

    Phase 1 — Validation + Setup
    Phase 2 — AI Intent Extraction (Gemini Call 1)
    Phase 3 — Rules Engine (deterministic)
    Phase 4 — AI Final Decision (Gemini Call 2, skipped on HARD_DENY)
    Phase 5 — Execute Decision
    """

    product = request.product
    chat_history = request.chat_history or ""

    # ── Phase 1: Validation + Setup ──────────────────────────────────────────

    # Step 2: Extract merchant domain
    merchant_domain = _extract_domain(product.merchant_url)

    # Step 3: Create Transaction row
    request_data = json.dumps(request.model_dump())
    transaction = Transaction(
        user_id=user_id,
        connection_key_id=connection_key_id,
        status="PENDING_EVALUATION",
        request_data=request_data,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Fire TRANSACTION_CREATED to Hedera (non-blocking, fire-and-forget)
    async def _fire_transaction_created():
        product_data = request.model_dump().get("product", {})
        payload = {
            "t":   transaction.id,
            "u":   transaction.user_id,
            "p":   str(product_data.get("product_name", ""))[:80],
            "amt": product_data.get("price"),
            "m":   merchant_domain,
            "ts":  transaction.created_at.isoformat(),
        }
        hedera_id = await hedera_service.submit_audit_message("TRANSACTION_CREATED", payload)
        if hedera_id:
            transaction.hedera_tx_id = hedera_id
            db.commit()

    asyncio.create_task(_fire_transaction_created())

    # Broadcast TRANSACTION_CREATED
    await ws_manager.send_to_user(user_id, {
        "type": "TRANSACTION_CREATED",
        "data": {
            "transaction_id": transaction.id,
            "product_name": product.product_name,
            "price": product.price,
            "merchant_name": product.merchant_name,
            "status": "PENDING_EVALUATION",
        },
    })

    # Step 4: Load profile's spending categories
    categories = db.query(SpendingCategory).filter(
        SpendingCategory.profile_id == profile_id
    ).all()

    if not categories:
        raise Exception("No spending categories configured for this profile")

    categories_for_gemini = [
        {
            "name": cat.name,
            "description": cat.description or "",
            "is_default": cat.is_default,
        }
        for cat in categories
    ]

    # ── Phase 2: AI Intent Extraction (Gemini Call 1) ────────────────────────

    # Step 5: Extract intent + category (NO product details — security isolation)
    call1_result = await extract_intent_and_category(chat_history, categories_for_gemini)

    # Step 6: Match category from Call 1 response
    category_name_from_gemini = call1_result.get("category", {}).get("name", "")
    matched_category = next(
        (c for c in categories if c.name == category_name_from_gemini), None
    )
    if not matched_category:
        matched_category = next((c for c in categories if c.is_default), None)
    if not matched_category:
        matched_category = categories[0]

    category_confidence = call1_result.get("category", {}).get("confidence", 0.5)
    intent_summary = call1_result.get("intent", {}).get("summary", "")

    # ── Phase 3: Rules Engine (Deterministic) ────────────────────────────────

    # Step 7: Calculate spending totals
    spending_totals = get_spending_totals(user_id, matched_category.id, db)

    # Step 8: Load rules + evaluate
    rules = db.query(CategoryRule).filter(
        CategoryRule.category_id == matched_category.id,
        CategoryRule.is_active == True,
    ).all()

    outcome, checks = evaluate_rules(
        rules=rules,
        price=product.price,
        merchant_domain=merchant_domain,
        spending_totals=spending_totals,
    )

    # ── Phase 4: AI Final Decision (Gemini Call 2) ───────────────────────────

    # Collect pending CUSTOM_RULE prompts for Call 2
    custom_rules_for_call2 = [
        {"rule_id": c["rule_id"], "prompt_text": c["prompt"]}
        for c in checks
        if c.get("status") == "pending_ai"
    ]

    decision = None
    ai_reasoning = None
    intent_match = None
    risk_flags = []
    custom_rule_results = []
    call2_confidence = 1.0

    if outcome == "HARD_DENY":
        # Skip Call 2 — rules already determined DENY
        decision = "DENY"
    else:
        # Step 9-10: Build report and call Gemini Call 2
        report = {
            "intent": call1_result.get("intent", {}),
            "category": {
                "name": matched_category.name,
                "confidence": category_confidence,
            },
            "product": {
                "product_name": product.product_name,
                "price": product.price,
                "currency": product.currency,
                "merchant_name": product.merchant_name,
                "merchant_url": product.merchant_url,
            },
            "rules_outcome": outcome,
            "rules_results": checks,
        }

        call2_result = await make_final_decision(report, custom_rules_for_call2 or None)

        decision = call2_result.get("decision", "HUMAN_NEEDED")
        ai_reasoning = call2_result.get("reasoning")
        intent_match = call2_result.get("intent_match")
        risk_flags = call2_result.get("risk_flags", [])
        custom_rule_results = call2_result.get("custom_rule_results", [])
        call2_confidence = call2_result.get("confidence", 0.0)

        # Update CUSTOM_RULE checks with Call 2 results
        for cr in custom_rule_results:
            for check in checks:
                if check.get("rule_id") == cr.get("rule_id"):
                    check["passed"] = cr.get("passed", False)
                    check["detail"] = cr.get("detail", check["detail"])
                    check["status"] = "evaluated"

    # ── Phase 5: Execute Decision ────────────────────────────────────────────

    # Step 11: Apply guardrails on Gemini's decision
    if outcome != "HARD_DENY" and decision == "APPROVE":
        # Guardrail 1: ALWAYS_REQUIRE_APPROVAL rule present — user explicitly set it
        if any(c.get("rule_type") == "ALWAYS_REQUIRE_APPROVAL" for c in checks):
            decision = "HUMAN_NEEDED"
        # Guardrail 2: AUTO_APPROVE_UNDER threshold not met (price >= threshold)
        if any(c.get("rule_type") == "AUTO_APPROVE_UNDER" and not c.get("passed", True) for c in checks):
            decision = "HUMAN_NEEDED"
        # Guardrail 3: AI not confident enough
        if call2_confidence < 0.7:
            decision = "HUMAN_NEEDED"
        # Guardrail 4: Product doesn't match user intent
        if intent_match is not None and intent_match < 0.5:
            decision = "HUMAN_NEEDED"
            risk_flags = list(risk_flags) + ["Low intent match — possible agent drift"]

    # Step 12: Create Evaluation row
    evaluation = Evaluation(
        transaction_id=transaction.id,
        category_id=matched_category.id,
        category_confidence=category_confidence,
        intent_match=intent_match,
        intent_summary=intent_summary,
        decision_reasoning=ai_reasoning,
        risk_flags=json.dumps(risk_flags),
        rules_checked=json.dumps(checks),
        decision=decision,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # Fire EVALUATION_DECIDED to Hedera (non-blocking, fire-and-forget)
    async def _fire_evaluation_decided():
        payload = {
            "t":      evaluation.transaction_id,
            "ev":     evaluation.id,
            "d":      evaluation.decision,
            "db":     "RULES" if outcome == "HARD_DENY" else "AI",
            "c":      matched_category.name,
            "conf":   evaluation.category_confidence,
            "intent": str(evaluation.intent_summary or "")[:100],
            "reason": str(evaluation.decision_reasoning or "")[:100],
            "rules":  outcome,   # ALL_PASS / SOFT_FLAGS / HARD_DENY
            "ts":     evaluation.created_at.isoformat(),
        }
        hedera_id = await hedera_service.submit_audit_message("EVALUATION_DECIDED", payload)
        if hedera_id:
            evaluation.hedera_tx_id = hedera_id
            db.commit()

    asyncio.create_task(_fire_evaluation_decided())

    reason = _build_reason(decision, checks, matched_category.name, ai_reasoning)
    virtual_card_response = None
    timeout_seconds = None

    if decision == "APPROVE":
        # Step 12: Issue virtual card
        transaction.status = "AI_APPROVED"
        db.commit()

        # Resolve payment method
        payment_method_id = matched_category.payment_method_id
        if not payment_method_id:
            default_pm = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_default == True,
                PaymentMethod.status == "active",
            ).first()
            if default_pm:
                payment_method_id = default_pm.id
        if not payment_method_id:
            any_pm = db.query(PaymentMethod).filter(
                PaymentMethod.user_id == user_id,
                PaymentMethod.status == "active",
            ).first()
            if any_pm:
                payment_method_id = any_pm.id
        if not payment_method_id:
            payment_method_id = "none"

        card_data = issue_mock_card(transaction.id, product.price, merchant_domain)

        virtual_card = VirtualCard(
            transaction_id=transaction.id,
            user_id=user_id,
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

        await ws_manager.send_to_user(user_id, {
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

        await ws_manager.send_to_user(user_id, {
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

        await ws_manager.send_to_user(user_id, {
            "type": "APPROVAL_REQUIRED",
            "data": {
                "transaction_id": transaction.id,
                "product_name": product.product_name,
                "price": product.price,
                "merchant_name": product.merchant_name,
                "category_name": matched_category.name,
                "reason": reason,
                "timeout_seconds": timeout_seconds,
            },
        })

    # ── Build response ───────────────────────────────────────────────────────

    category_info = CategoryInfo(
        id=matched_category.id,
        name=matched_category.name,
        confidence=category_confidence,
    )

    rules_applied = [RuleResult(**check) for check in checks]

    ai_eval = AIEvaluation(
        category_name=matched_category.name,
        category_confidence=category_confidence,
        intent_match=intent_match,
        intent_summary=intent_summary,
        risk_flags=risk_flags,
        reasoning=ai_reasoning,
    )

    logger.info(
        f"Evaluate: txn={transaction.id} decision={decision} "
        f"category={matched_category.name} price={product.price}"
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
        hedera_tx_id=transaction.hedera_tx_id,
    )
