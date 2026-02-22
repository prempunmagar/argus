import json
import logging

logger = logging.getLogger(__name__)


def evaluate_rules(
    rules: list,            # list of CategoryRule ORM objects
    price: float,
    merchant_domain: str,
    spending_totals: dict,  # {"daily": float, "weekly": float, "monthly": float}
) -> tuple:
    """
    Evaluate all active rules against the transaction.

    Returns (outcome: str, checks: list[dict]).
    outcome is one of "HARD_DENY" | "SOFT_FLAGS" | "ALL_PASS".

    This is a deterministic classifier — it does NOT make the final decision.
    Gemini Call 2 makes the final decision using these results.

    Outcome logic:
      - Any hard fail → HARD_DENY
      - Any soft flag → SOFT_FLAGS
      - All pass → ALL_PASS
    """
    checks = []
    has_hard_fail = False
    has_soft_flags = False

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
            previously_spent = spending_totals.get("daily", 0.0)
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

        # ── WEEKLY_LIMIT ────────────────────────────────────────────────────
        elif rtype == "WEEKLY_LIMIT":
            threshold = float(raw_value)
            previously_spent = spending_totals.get("weekly", 0.0)
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

        # ── MONTHLY_LIMIT ───────────────────────────────────────────────────
        elif rtype == "MONTHLY_LIMIT":
            threshold = float(raw_value)
            previously_spent = spending_totals.get("monthly", 0.0)
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

        # ── MERCHANT_BLACKLIST ──────────────────────────────────────────────
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

        # ── MERCHANT_WHITELIST ──────────────────────────────────────────────
        elif rtype == "MERCHANT_WHITELIST":
            try:
                whitelist = json.loads(raw_value)
            except Exception:
                whitelist = [raw_value]
            passed = merchant_domain in whitelist
            if not passed:
                has_hard_fail = True  # v2: whitelist miss → HARD_DENY
            checks.append({
                "rule_type": rtype,
                "merchant_domain": merchant_domain,
                "passed": passed,
                "detail": (
                    f"Merchant {merchant_domain} is on the approved whitelist."
                    if passed
                    else f"Merchant {merchant_domain} is not on the approved whitelist — denied."
                ),
            })

        # ── AUTO_APPROVE_UNDER ──────────────────────────────────────────────
        elif rtype == "AUTO_APPROVE_UNDER":
            threshold = float(raw_value)
            passed = price < threshold  # strict less-than per spec
            if not passed:
                has_soft_flags = True
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

        # ── ALWAYS_REQUIRE_APPROVAL ─────────────────────────────────────────
        elif rtype == "ALWAYS_REQUIRE_APPROVAL":
            has_soft_flags = True
            checks.append({
                "rule_type": rtype,
                "passed": False,
                "detail": "This category always requires human approval.",
            })

        # ── CUSTOM_RULE ─────────────────────────────────────────────────────
        elif rtype == "CUSTOM_RULE":
            # Not evaluated here — recorded as pending_ai for Gemini Call 2
            has_soft_flags = True
            checks.append({
                "rule_type": rtype,
                "rule_id": rule.id,
                "prompt": raw_value,  # the free-text condition
                "status": "pending_ai",
                "passed": False,  # pending = not yet passed
                "detail": f"Custom rule pending AI evaluation: {raw_value}",
            })

        else:
            logger.warning(f"Unknown rule type: {rtype!r} — skipping")

    # ── Outcome classification ──────────────────────────────────────────────
    if has_hard_fail:
        outcome = "HARD_DENY"
    elif has_soft_flags:
        outcome = "SOFT_FLAGS"
    else:
        outcome = "ALL_PASS"

    return outcome, checks
