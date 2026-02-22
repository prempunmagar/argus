from pydantic import BaseModel
from typing import Optional, List, Any


# ── Sub-objects ───────────────────────────────────────────────────────────────

class TransactionRequestData(BaseModel):
    """Parsed fields from the request_data JSON blob."""
    product_name: str
    price: float
    currency: str = "USD"
    merchant_name: str
    merchant_url: Optional[str] = None
    merchant_domain: Optional[str] = None   # extracted on the fly from merchant_url
    product_url: Optional[str] = None
    conversation_context: Optional[str] = None


class TransactionEvaluationSummary(BaseModel):
    """Slim evaluation fields for the list view."""
    decision: Optional[str] = None          # APPROVE | DENY | HUMAN_NEEDED
    category_name: Optional[str] = None
    category_confidence: Optional[float] = None
    intent_match: Optional[float] = None


class TransactionEvaluationDetail(BaseModel):
    """Full evaluation record for the detail view."""
    id: str
    decision: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_confidence: Optional[float] = None
    intent_match: Optional[float] = None
    intent_summary: Optional[str] = None
    decision_reasoning: Optional[str] = None
    risk_flags: List[str] = []
    rules_checked: List[Any] = []
    hedera_tx_id: Optional[str] = None  # Hedera TX for EVALUATION_DECIDED event
    created_at: str


class VirtualCardDetail(BaseModel):
    """Full virtual card details returned when transaction is approved."""
    card_number: str
    expiry_month: str
    expiry_year: str
    cvv: str
    last_four: str
    spend_limit: float
    merchant_lock: Optional[str] = None
    expires_at: str
    status: str


# ── GET /transactions (list) ──────────────────────────────────────────────────

class TransactionListItem(BaseModel):
    id: str
    status: str
    request_data: TransactionRequestData
    evaluation: Optional[TransactionEvaluationSummary] = None
    virtual_card_last_four: Optional[str] = None
    virtual_card_status: Optional[str] = None
    created_at: str


class TransactionListResponse(BaseModel):
    transactions: List[TransactionListItem]
    total: int
    limit: int
    offset: int


# ── GET /transactions/{id} (detail) ──────────────────────────────────────────

class TransactionDetail(BaseModel):
    id: str
    status: str
    request_data: TransactionRequestData
    evaluation: Optional[TransactionEvaluationDetail] = None
    virtual_card: Optional[VirtualCardDetail] = None
    hedera_tx_id: Optional[str] = None  # Hedera TX for TRANSACTION_CREATED event
    created_at: str
    updated_at: str


# ── GET /transactions/{id}/status (plugin polling) ────────────────────────────

class TransactionStatusResponse(BaseModel):
    transaction_id: str
    status: str
    decision: Optional[str] = None
    reason: Optional[str] = None
    virtual_card: Optional[VirtualCardDetail] = None
    waited_seconds: Optional[int] = None
    timeout_seconds: int = 300


# ── POST /transactions/{id}/respond ──────────────────────────────────────────

class RespondRequest(BaseModel):
    action: str            # "APPROVE" or "DENY"
    note: Optional[str] = None   # optional user note


class RespondResponse(BaseModel):
    transaction_id: str
    action: str            # "APPROVE" or "DENY"
    reason: str
    virtual_card: Optional[VirtualCardDetail] = None
    hedera_tx_id: Optional[str] = None  # Hedera TX for HUMAN_APPROVAL_RESPONSE event
