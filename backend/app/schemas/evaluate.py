from pydantic import BaseModel
from typing import Optional


# --- Request ---

class EvaluateMetadata(BaseModel):
    """Optional metadata about the calling agent."""
    agent_framework: Optional[str] = None
    agent_name: Optional[str] = None
    session_id: Optional[str] = None


class EvaluateRequest(BaseModel):
    """
    Request body for POST /evaluate.
    Sent by the ADK plugin when the agent calls request_purchase.
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
    """Category detected by Gemini, included in every evaluate response."""
    id: str
    name: str
    confidence: float


class RuleBreakdown(BaseModel):
    """Spending breakdown for limit-type rules (daily, weekly, monthly)."""
    previously_spent: float
    this_transaction: float


class RuleResult(BaseModel):
    """
    Result of a single rule check.
    Every rule that was evaluated gets one of these in rules_applied.
    """
    rule_type: str
    threshold: Optional[float] = None
    actual: Optional[float] = None
    breakdown: Optional[RuleBreakdown] = None
    merchant_domain: Optional[str] = None
    passed: bool
    detail: str


class AIEvaluation(BaseModel):
    """Gemini's evaluation of the purchase request."""
    category_name: str
    category_confidence: float
    intent_match: float
    intent_summary: str
    risk_flags: list[str]
    reasoning: str


class VirtualCardResponse(BaseModel):
    """Virtual card details, only present when decision is APPROVE."""
    card_number: str
    expiry_month: str
    expiry_year: str
    cvv: str
    last_four: str
    spend_limit: float
    merchant_lock: Optional[str] = None
    expires_at: str  # ISO format


class ApprovalInfo(BaseModel):
    """Approval URLs, only present when decision is REQUIRE_APPROVAL."""
    timeout_seconds: int
    poll_url: str
    approve_url: str
    deny_url: str


# --- Main response ---

class EvaluateResponse(BaseModel):
    """
    Response from POST /evaluate.
    Always includes transaction_id, decision, reason, category, rules_applied, ai_evaluation.
    virtual_card is only present when decision is APPROVE.
    approval is only present when decision is REQUIRE_APPROVAL.
    """
    transaction_id: str
    decision: str  # "APPROVE", "DENY", or "REQUIRE_APPROVAL"
    reason: str
    category: CategoryInfo
    rules_applied: list[RuleResult]
    ai_evaluation: AIEvaluation
    virtual_card: Optional[VirtualCardResponse] = None
    approval: Optional[ApprovalInfo] = None
