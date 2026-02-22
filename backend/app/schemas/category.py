from pydantic import BaseModel
from typing import Optional, List


# ── Sub-objects ────────────────────────────────────────────────────────────────

class CategoryRuleItem(BaseModel):
    """A single rule row (active rules only in GET responses)."""
    id: str
    rule_type: str
    value: str
    is_active: bool


class PaymentMethodSummary(BaseModel):
    """Slim payment method info embedded in category response."""
    id: str
    nickname: str
    method_type: str


# ── Category response (used by GET list + POST/PUT returns) ────────────────────

class CategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool
    payment_method: Optional[PaymentMethodSummary] = None
    rules: List[CategoryRuleItem] = []
    spending_today: float = 0.0
    spending_this_week: float = 0.0
    spending_this_month: float = 0.0


class CategoriesListResponse(BaseModel):
    categories: List[CategoryResponse]


# ── Rule input (used in POST and PUT bodies) ───────────────────────────────────

class CreateRuleRequest(BaseModel):
    rule_type: str
    value: str


# ── POST /categories ───────────────────────────────────────────────────────────

class CreateCategoryRequest(BaseModel):
    profile_id: str
    name: str
    description: Optional[str] = None
    payment_method_id: Optional[str] = None
    rules: List[CreateRuleRequest] = []


# ── PUT /categories/{id} ───────────────────────────────────────────────────────

class UpdateCategoryRequest(BaseModel):
    """All fields optional — only provided fields are updated."""
    name: Optional[str] = None
    description: Optional[str] = None
    payment_method_id: Optional[str] = None
    rules: Optional[List[CreateRuleRequest]] = None  # None = don't touch rules
