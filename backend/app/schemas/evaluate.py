from pydantic import BaseModel
from typing import Optional, List


# --- Request ---

class ProductInfo(BaseModel):
    """Nested product details within EvaluateRequest."""
    product_name: str
    price: float
    currency: str = "USD"
    merchant_name: str
    merchant_url: str
    product_url: Optional[str] = None
    notes: Optional[str] = None


class EvaluateRequest(BaseModel):
    """
    Request body for POST /evaluate.
    Nested structure: product details + chat history.
    """
    product: ProductInfo
    chat_history: str = ""


# --- Response sub-objects ---

class CategoryInfo(BaseModel):
    id: str
    name: str
    confidence: float


class RuleResult(BaseModel):
    """Result of a single rule check included in rules_applied."""
    rule_type: str
    threshold: Optional[float] = None
    actual: Optional[float] = None
    breakdown: Optional[dict] = None   # {"previously_spent": x, "this_transaction": y} for limit rules
    merchant_domain: Optional[str] = None
    rule_id: Optional[str] = None      # for CUSTOM_RULE
    prompt: Optional[str] = None       # for CUSTOM_RULE
    status: Optional[str] = None       # for CUSTOM_RULE: "pending_ai"
    passed: bool
    detail: str


class AIEvaluation(BaseModel):
    category_name: Optional[str] = None
    category_confidence: Optional[float] = None
    intent_match: Optional[float] = None
    intent_summary: Optional[str] = None
    risk_flags: List[str] = []
    reasoning: Optional[str] = None


class VirtualCardResponse(BaseModel):
    """Returned only when decision is APPROVE."""
    card_number: str
    expiry_month: str
    expiry_year: str
    cvv: str
    last_four: str
    spend_limit: float
    merchant_lock: Optional[str] = None
    expires_at: str  # ISO format


# --- Main response ---

class EvaluateResponse(BaseModel):
    """
    Response from POST /evaluate.
    decision: "APPROVE" | "DENY" | "HUMAN_NEEDED"
    virtual_card: present only when APPROVE
    timeout_seconds: present only when HUMAN_NEEDED
    """
    transaction_id: str
    decision: str
    reason: str
    category: Optional[CategoryInfo] = None
    rules_applied: List[RuleResult] = []
    ai_evaluation: Optional[AIEvaluation] = None
    virtual_card: Optional[VirtualCardResponse] = None
    timeout_seconds: Optional[int] = None  # only when HUMAN_NEEDED
