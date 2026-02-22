import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

# Statuses that count toward spending totals for limit rules
_APPROVED_STATUSES = {"AI_APPROVED", "HUMAN_APPROVED", "COMPLETED"}


def get_spending_total(db: Session, category_id: str, since: datetime) -> float:
    """
    Sum the price of all approved transactions for a category since `since`.
    Joins evaluations → transactions and parses price from request_data JSON.
    """
    rows = (
        db.query(Evaluation, Transaction)
        .join(Transaction, Transaction.id == Evaluation.transaction_id)
        .filter(
            Evaluation.category_id == category_id,
            Evaluation.decision.in_(list(_APPROVED_STATUSES)),
            Evaluation.created_at >= since,
        )
        .all()
    )

    total = 0.0
    for evaluation, transaction in rows:
        try:
            data = json.loads(transaction.request_data)
            total += float(data.get("price", 0))
        except Exception:
            pass
    return round(total, 2)


def run_rules(
    db: Session,
    rules: list,            # list of CategoryRule ORM objects
    category_id: str,
    price: float,
    merchant_domain: str,
    gemini_result: dict,    # output of call_gemini()
) -> tuple:
    """
    Evaluate all active rules against the transaction.

    Returns (checks: list[dict], decision: str).
    decision is one of "APPROVE", "DENY", "HUMAN_NEEDED".

    Decision priority (spec Section 3.4 / CLAUDE.md):
      1. BLOCK_CATEGORY or hard-fail → DENY
      2. CUSTOM_RULE fail / ALWAYS_REQUIRE_APPROVAL / AUTO_APPROVE_UNDER fail /
         MERCHANT_WHITELIST fail / AI risk flags → HUMAN_NEEDED
      3. All pass → APPROVE
    """
    checks = []
    has_hard_fail = False
    requires_approval = False

    now = datetime.now(timezone.utc)

    for rule in rules:
        if not rule.is_active:
            continue

        rtype = rule.rule_type
        raw_value = rule.value

        # ── BLOCK_CATEGORY ──────────────────────────────────────────────────
        if rtype == "BLOCK_CATEGORY":
            if raw_value.lower() == "true":
                has_hard_fail = True
                checks.append({
                    "rule_type": rtype,
                    "passed": False,
                    "detail": "This category is blocked — all purchases denied.",
                })
            else:
                checks.append({
                    "rule_type": rtype,
                    "passed": True,
                    "detail": "BLOCK_CATEGORY is inactive (value=false).",
                })

        # ── MAX_PER_TRANSACTION ─────────────────────────────────────────────
        elif rtype == "MAX_PER_TRANSACTION":
            threshold = float(raw_value)
            passed = price <= threshold
            if not passed:
                has_hard_fail = True
            checks.append({
                "rule_type": rtype,
                "threshold": threshold,
                "actual": price,
                "passed": passed,
                "detail": (
                    f"Price ${price} is within per-transaction limit ${threshold}."
                    if passed
                    else f"Price ${price} exceeds per-transaction limit ${threshold}."
                ),
            })

        # ── DAILY_LIMIT ─────────────────────────────────────────────────────
        elif rtype == "DAILY_LIMIT":
            threshold = float(raw_value)
            since = now - timedelta(days=1)
            previously_spent = get_spending_total(db, category_id, since)
            total_if_approved = round(previously_spent + price, 2)
            passed = total_if_approved <= threshold
            if not passed:
                has_hard_fail = True
            checks.append({
                "rule_type": rtype,
                "threshold": threshold,
                "actual": total_if_approved,
                "breakdown": {"previously_spent": previously_spent, "this_transaction": price},
                "passed": passed,
                "detail": (
                    f"Daily spend ${total_if_approved} is within limit ${threshold}."
                    if passed
                    else f"Daily spend ${total_if_approved} would exceed limit ${threshold}."
                ),
            })

        # ── WEEKLY_LIMIT ─────────────────────────────────────────────────────
        elif rtype == "WEEKLY_LIMIT":
            threshold = float(raw_value)
            since = now - timedelta(weeks=1)
            previously_spent = get_spending_total(db, category_id, since)
            total_if_approved = round(previously_spent + price, 2)
            passed = total_if_approved <= threshold
            if not passed:
                has_hard_fail = True
            checks.append({
                "rule_type": rtype,
                "threshold": threshold,
                "actual": total_if_approved,
                "breakdown": {"previously_spent": previously_spent, "this_transaction": price},
                "passed": passed,
                "detail": (
                    f"Weekly spend ${total_if_approved} is within limit ${threshold}."
                    if passed
                    else f"Weekly spend ${total_if_approved} would exceed limit ${threshold}."
                ),
            })

        # ── MONTHLY_LIMIT ─────────────────────────────────────────────────────
        elif rtype == "MONTHLY_LIMIT":
            threshold = float(raw_value)
            since = now - timedelta(days=30)
            previously_spent = get_spending_total(db, category_id, since)
            total_if_approved = round(previously_spent + price, 2)
            passed = total_if_approved <= threshold
            if not passed:
                has_hard_fail = True
            checks.append({
                "rule_type": rtype,
                "threshold": threshold,
                "actual": total_if_approved,
                "breakdown": {"previously_spent": previously_spent, "this_transaction": price},
                "passed": passed,
                "detail": (
                    f"Monthly spend ${total_if_approved} is within limit ${threshold}."
                    if passed
                    else f"Monthly spend ${total_if_approved} would exceed limit ${threshold}."
                ),
            })

        # ── MERCHANT_BLACKLIST ───────────────────────────────────────────────
        elif rtype == "MERCHANT_BLACKLIST":
            try:
                blacklist = json.loads(raw_value)
            except Exception:
                blacklist = [raw_value]
            passed = merchant_domain not in blacklist
            if not passed:
                has_hard_fail = True
            checks.append({
                "rule_type": rtype,
                "merchant_domain": merchant_domain,
                "passed": passed,
                "detail": (
                    f"Merchant {merchant_domain} is not blacklisted."
                    if passed
                    else f"Merchant {merchant_domain} is blacklisted."
                ),
            })

        # ── MERCHANT_WHITELIST ───────────────────────────────────────────────
        elif rtype == "MERCHANT_WHITELIST":
            try:
                whitelist = json.loads(raw_value)
            except Exception:
                whitelist = [raw_value]
            passed = merchant_domain in whitelist
            if not passed:
                requires_approval = True
            checks.append({
                "rule_type": rtype,
                "merchant_domain": merchant_domain,
                "passed": passed,
                "detail": (
                    f"Merchant {merchant_domain} is on the approved whitelist."
                    if passed
                    else f"Merchant {merchant_domain} is not on the approved whitelist — requires review."
                ),
            })

        # ── AUTO_APPROVE_UNDER ───────────────────────────────────────────────
        elif rtype == "AUTO_APPROVE_UNDER":
            threshold = float(raw_value)
            passed = price < threshold  # strict less-than per spec
            if not passed:
                requires_approval = True
            checks.append({
                "rule_type": rtype,
                "threshold": threshold,
                "actual": price,
                "passed": passed,
                "detail": (
                    f"Price ${price} is under auto-approve threshold ${threshold}."
                    if passed
                    else f"Price ${price} meets or exceeds auto-approve threshold ${threshold} — requires review."
                ),
            })

        # ── ALWAYS_REQUIRE_APPROVAL ──────────────────────────────────────────
        elif rtype == "ALWAYS_REQUIRE_APPROVAL":
            requires_approval = True
            checks.append({
                "rule_type": rtype,
                "passed": False,
                "detail": "This category always requires human approval.",
            })

        # ── CUSTOM_RULE ──────────────────────────────────────────────────────
        elif rtype == "CUSTOM_RULE":
            custom_results = gemini_result.get("custom_rule_results", [])
            gemini_check = next(
                (r for r in custom_results if r.get("rule_id") == rule.id), None
            )
            if gemini_check:
                passed = gemini_check.get("passed", False)
                detail = gemini_check.get("detail", "No detail provided.")
            else:
                passed = False
                detail = "Custom rule was not evaluated by AI — defaulting to fail."
            if not passed:
                requires_approval = True
            checks.append({
                "rule_type": rtype,
                "passed": passed,
                "detail": detail,
            })

        else:
            logger.warning(f"Unknown rule type: {rtype!r} — skipping")

    # ── Gemini intent / risk check ───────────────────────────────────────────
    intent_match = gemini_result.get("intent_match", 1.0)
    risk_flags = gemini_result.get("risk_flags", [])

    if intent_match < 0.5 or risk_flags:
        requires_approval = True
        flag_summary = "; ".join(risk_flags) if risk_flags else "none"
        checks.append({
            "rule_type": "AI_RISK_CHECK",
            "passed": False,
            "detail": (
                f"AI flagged concerns: intent_match={intent_match:.2f}, "
                f"risk_flags=[{flag_summary}]"
            ),
        })

    # ── Final decision ───────────────────────────────────────────────────────
    if has_hard_fail:
        decision = "DENY"
    elif requires_approval:
        decision = "HUMAN_NEEDED"
    else:
        decision = "APPROVE"

    return checks, decision
