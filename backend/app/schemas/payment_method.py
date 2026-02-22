from pydantic import BaseModel
from typing import Optional, List, Any


# ── Payment method schemas ─────────────────────────────────────────────────────

class PaymentMethodResponse(BaseModel):
    id: str
    nickname: str
    method_type: str
    status: str
    is_default: bool
    detail: Any = {}   # type-specific JSON (brand, last4, etc.)


class PaymentMethodsListResponse(BaseModel):
    payment_methods: List[PaymentMethodResponse]


class CreatePaymentMethodRequest(BaseModel):
    method_type: str           # CARD, BANK_ACCOUNT, CRYPTO_WALLET
    nickname: str
    is_default: bool = False
    detail: Any = {}           # type-specific data per spec Section 2.3
