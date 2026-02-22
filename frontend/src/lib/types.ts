// === Auth ===
export interface User {
  id: string
  email: string
  name: string
  created_at: string
}

export interface AuthResponse {
  user: User
  token: string
}

// === Profiles ===
export interface Profile {
  id: string
  name: string
  description?: string
  is_active: boolean
  created_at: string
}

// === Transaction Status Lifecycle ===
export type TransactionStatus =
  | "PENDING_EVALUATION"
  | "AI_APPROVED"
  | "AI_DENIED"
  | "HUMAN_NEEDED"
  | "HUMAN_APPROVED"
  | "HUMAN_DENIED"
  | "HUMAN_TIMEOUT"
  | "COMPLETED"
  | "EXPIRED"
  | "FAILED"

export type Decision = "APPROVE" | "DENY" | "HUMAN_NEEDED"

// === Rules ===
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
  | "CUSTOM_RULE"

export interface CategoryRule {
  id: string
  rule_type: RuleType
  value: string
  is_active: boolean
}

// === Rule Check (from evaluation) ===
export interface RuleCheck {
  rule_id: string
  rule_type: string
  threshold?: number
  actual_value?: number
  breakdown?: { previously_spent: number; this_transaction: number }
  prompt?: string
  merchant_domain?: string
  whitelist?: string[]
  passed: boolean
  detail: string
}

// === AI Evaluation ===
export interface AIEvaluation {
  category_name: string
  category_confidence: number
  intent_match: number
  intent_summary: string
  risk_flags: string[]
  reasoning: string
}

// === Virtual Card ===
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

// === Payment Methods ===
export interface PaymentMethod {
  id: string
  nickname: string
  method_type: "CARD" | "BANK_ACCOUNT" | "CRYPTO_WALLET"
  status: string
  is_default: boolean
  detail: Record<string, any>
}

// === Spending Categories ===
export interface SpendingCategory {
  id: string
  name: string
  description?: string
  is_default: boolean
  payment_method?: { id: string; nickname: string; method_type: string }
  rules: CategoryRule[]
  spending_today: number
  spending_this_week: number
  spending_this_month: number
}

export interface CategoriesResponse {
  categories: SpendingCategory[]
}

// === Connection Keys ===
export interface ConnectionKey {
  id: string
  key_prefix: string
  key_value?: string
  label: string
  is_active: boolean
  expires_at?: string
  last_used_at: string | null
  created_at: string
}

// === Transaction request_data (stored as JSON on transaction) ===
export interface RequestData {
  product_name: string
  product_url?: string
  price: number
  currency: string
  merchant_name: string
  merchant_domain: string
  merchant_url: string
  conversation_context?: string
  metadata?: Record<string, any>
}

// === Evaluation summary (joined from evaluations table) ===
export interface EvaluationSummary {
  decision: Decision
  category_name?: string
  category_confidence?: number
  intent_match?: number
  intent_summary?: string
  decision_reasoning?: string
  risk_flags?: string[]
  rules_checked?: RuleCheck[]
}

// === Transaction (list item from GET /transactions) ===
export interface Transaction {
  id: string
  status: TransactionStatus
  request_data: RequestData
  evaluation?: EvaluationSummary
  virtual_card_last_four?: string
  virtual_card_status?: string
  created_at: string
  updated_at?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  limit: number
  offset: number
}

// === Transaction detail (full view with virtual card) ===
export interface TransactionDetail {
  id: string
  status: TransactionStatus
  request_data: RequestData
  evaluation?: EvaluationSummary
  ai_evaluation?: AIEvaluation
  virtual_card?: VirtualCard
  created_at: string
  updated_at?: string
}

// === WebSocket Messages ===
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
