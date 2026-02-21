export interface User {
  id: string
  email: string
  name: string
  created_at: string
}

export interface Agent {
  id: string
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  user: User
  token: string
}

export type TransactionStatus =
  | "PENDING_EVALUATION"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "DENIED"
  | "COMPLETED"
  | "EXPIRED"
  | "FAILED"

export type Decision = "APPROVE" | "DENY" | "REQUIRE_APPROVAL"

export interface TransactionListItem {
  id: string
  status: TransactionStatus
  product_name: string
  price: number
  currency: string
  merchant_name: string
  merchant_domain: string
  detected_category_name: string | null
  decision: Decision | null
  decision_reason: string | null
  virtual_card_last_four: string | null
  virtual_card_status: string | null
  created_at: string
  decided_at: string | null
}

export interface TransactionListResponse {
  transactions: TransactionListItem[]
  total: number
  limit: number
  offset: number
}

export interface RuleCheck {
  rule_id: string
  rule_type: RuleType
  threshold?: number
  actual_value?: number
  breakdown?: { previously_spent: number; this_transaction: number }
  merchant_domain?: string
  whitelist?: string[]
  passed: boolean
  detail: string
}

export interface AIEvaluation {
  category_name: string
  category_confidence: number
  intent_match: number
  intent_summary: string
  risk_flags: string[]
  reasoning: string
}

export interface VirtualCard {
  card_number: string
  expiry_month: string
  expiry_year: string
  cvv: string
  last_four: string
  spend_limit: number
  merchant_lock: string | null
  expires_at: string
}

export interface TransactionDetail {
  id: string
  status: TransactionStatus
  product_name: string
  product_url: string | null
  price: number
  currency: string
  merchant_name: string
  merchant_url: string
  merchant_domain: string
  conversation_context: string | null
  detected_category_id: string | null
  detected_category_name: string | null
  category_confidence: number | null
  rules_checked: RuleCheck[] | null
  ai_evaluation: AIEvaluation | null
  decision: Decision | null
  decision_reason: string | null
  decided_at: string | null
  approval_requested_at: string | null
  approval_responded_at: string | null
  approved_by: string | null
  virtual_card: VirtualCard | null
  created_at: string
  updated_at: string
}

export type RuleType =
  | "MAX_PER_TRANSACTION"
  | "DAILY_LIMIT"
  | "WEEKLY_LIMIT"
  | "MONTHLY_LIMIT"
  | "AUTO_APPROVE_UNDER"
  | "MERCHANT_WHITELIST"
  | "MERCHANT_BLACKLIST"
  | "ALWAYS_REQUIRE_APPROVAL"
  | "BLOCK_CATEGORY"

export interface CategoryRule {
  id: string
  rule_type: RuleType
  value: string
  is_active: boolean
}

export interface PaymentMethod {
  id: string
  label: string
  type: "CREDIT_CARD" | "DEBIT_CARD" | "BANK_ACCOUNT" | "CRYPTO_WALLET"
  provider: string
  is_default: boolean
  is_active: boolean
}

export interface SpendingCategory {
  id: string
  name: string
  description: string | null
  keywords: string[]
  is_default: boolean
  display_order: number
  payment_method: PaymentMethod | null
  rules: CategoryRule[]
  spending_today: number
  spending_this_week: number
  spending_this_month: number
}

export interface CategoriesResponse {
  categories: SpendingCategory[]
}

export interface AgentKey {
  id: string
  key_prefix: string
  key_value?: string
  label: string
  is_active: boolean
  last_used_at: string | null
  created_at: string
}

// WebSocket message types
export type WSMessageType =
  | "TRANSACTION_CREATED"
  | "TRANSACTION_DECIDED"
  | "APPROVAL_REQUIRED"
  | "VIRTUAL_CARD_USED"

export interface WSTransactionCreated {
  type: "TRANSACTION_CREATED"
  data: {
    transaction_id: string
    product_name: string
    price: number
    merchant_name: string
    status: "PENDING_EVALUATION"
  }
}

export interface WSTransactionDecided {
  type: "TRANSACTION_DECIDED"
  data: {
    transaction_id: string
    decision: Decision
    reason: string
    category_name: string
    virtual_card_last_four: string | null
  }
}

export interface WSApprovalRequired {
  type: "APPROVAL_REQUIRED"
  data: {
    transaction_id: string
    product_name: string
    price: number
    merchant_name: string
    category_name: string
    reason: string
    timeout_seconds: number
  }
}

export interface WSVirtualCardUsed {
  type: "VIRTUAL_CARD_USED"
  data: {
    transaction_id: string
    card_last_four: string
    amount: number
  }
}

export type WSMessage =
  | WSTransactionCreated
  | WSTransactionDecided
  | WSApprovalRequired
  | WSVirtualCardUsed
