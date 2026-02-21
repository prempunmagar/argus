# Import all models so that Base.metadata knows about every table.
# This file is imported once (e.g., in main.py) and that's enough
# for SQLAlchemy to discover all 10 tables when we call create_all().

from app.models.user import User
from app.models.profile import Profile
from app.models.payment_method import PaymentMethod
from app.models.spending_category import SpendingCategory
from app.models.category_rule import CategoryRule
from app.models.connection_key import ConnectionKey
from app.models.transaction import Transaction
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.virtual_card import VirtualCard

__all__ = [
    "User",
    "Profile",
    "PaymentMethod",
    "SpendingCategory",
    "CategoryRule",
    "ConnectionKey",
    "Transaction",
    "Evaluation",
    "HumanApproval",
    "VirtualCard",
]
