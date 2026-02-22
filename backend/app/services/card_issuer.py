import hashlib
from datetime import datetime, timedelta, timezone


def issue_mock_card(transaction_id: str, price: float, merchant_domain: str) -> dict:
    """
    Generate a deterministic mock virtual card from the transaction_id hash.
    Spec Section 7.2 — 15% spend limit buffer, 30-min expiry, merchant lock.
    """
    seed = hashlib.sha256(transaction_id.encode()).hexdigest()

    digits = "".join(str(int(c, 16) % 10) for c in seed[:12])
    card_number = "4532" + digits              # Visa-like 16-digit number
    cvv = str(int(seed[:3], 16) % 900 + 100)  # 3-digit CVV (100-999)
    spend_limit = round(price * 1.15, 2)       # 15% buffer for tax/shipping

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=30)

    return {
        "card_number": card_number,
        "expiry_month": "03",
        "expiry_year": "2026",
        "cvv": cvv,
        "last_four": card_number[-4:],
        "spend_limit": spend_limit,
        "spend_limit_buffer": round(spend_limit - price, 2),
        "merchant_lock": merchant_domain,
        "external_card_id": f"mock_{transaction_id[:8]}",
        "status": "ACTIVE",
        "issued_at": now,
        "expires_at": expires_at,
        "expires_at_iso": expires_at.isoformat(),
    }
