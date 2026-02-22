from pydantic import BaseModel
from typing import Optional, List


# --- Request ---

class EvaluateMetadata(BaseModel):
    agent_framework: Optional[str] = None
    agent_name: Optional[str] = None
    session_id: Optional[str] = None


class EvaluateRequest(BaseModel):
    """
    Request body for POST /evaluate.
    Required: product_name, price, merchant_name, merchant_url
    """
    product_name: str
    product_url: Optional[str] = None
    price: float
    currency: str = "USD"
    merchant_name: str
    merchant_url: str
    conversation_context: Optional[str] = None
    metadata: Optional[EvaluateMetadata] = None


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
