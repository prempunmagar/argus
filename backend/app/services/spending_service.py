import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

# Statuses that count toward spending totals for limit rules
_APPROVED_STATUSES = {"AI_APPROVED", "HUMAN_APPROVED", "COMPLETED"}


def _get_spending_since(db: Session, category_id: str, since: datetime) -> float:
    """
    Sum the price of all approved transactions for a category since `since`.
    Joins evaluations → transactions and parses price from request_data JSON.
    Supports both nested format (product.price) and flat format (price).
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
            # Support nested format: {product: {price: ...}}
            if "product" in data and isinstance(data["product"], dict):
                total += float(data["product"].get("price", 0))
            else:
                # Flat format: {price: ...}
                total += float(data.get("price", 0))
        except Exception:
            pass
    return round(total, 2)


def get_spending_totals(user_id: str, category_id: str, db: Session) -> dict:
    """
    Compute daily, weekly, and monthly spending totals for a category.

    Uses calendar boundaries:
      - daily:   today at midnight UTC
      - weekly:  this Monday at 00:00 UTC
      - monthly: 1st of this month at 00:00 UTC

    Queries previously approved transactions from the database — does NOT
    include the current request's price. The rules engine compares the
    current price against these totals.

    Returns: {"daily": float, "weekly": float, "monthly": float}
    """
    now = datetime.now(timezone.utc)

    # Calendar boundaries
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - __import__("datetime").timedelta(days=now.weekday())  # Monday
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return {
        "daily": _get_spending_since(db, category_id, start_of_day),
        "weekly": _get_spending_since(db, category_id, start_of_week),
        "monthly": _get_spending_since(db, category_id, start_of_month),
    }
