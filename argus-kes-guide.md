# ARGUS — Backend Builder's Guide
## Everything You Need to Build the Backend, Plugin, A2A & Deploy
### Owner: Teammate

---

## Your Scope

You own everything on the server side:

1. **Argus Core API** — FastAPI, all endpoints, all services, database
2. **Argus ADK Plugin** — `before_tool_callback` that intercepts agent purchase calls
3. **A2A Endpoint** — Google's Agent-to-Agent protocol for discoverability
4. **Database** — SQLAlchemy models, seed data
5. **Deployment** — Docker, Dockploy (backend), Vercel config (frontend)
6. **Documentation** — README.md setup instructions, ARCHITECTURE.md

**You do NOT touch:** `frontend/`, `agent/shopping_agent/`, `agent/run_agent.py`, pitch materials

---

## How Your Code Gets Used

There are two consumers of your API:

1. **The ADK Plugin** (which you also build) — calls `POST /evaluate` with agent key auth when the shopping agent wants to buy something. Also polls `GET /transactions/{id}/status` during human approval flow.

2. **The React Dashboard** (Prem builds) — calls all other endpoints with JWT auth. Login, list transactions, view categories, approve/deny purchases, manage connection keys. Also connects via WebSocket for real-time updates.

The plugin and dashboard never talk to each other directly. They both talk to your API, and your API coordinates everything (including pushing WebSocket updates when things change).

---

## PART 1: ARGUS CORE API

### 1.1 Project Setup

```bash
mkdir -p backend/app/{models,schemas,routers,services}
mkdir -p backend/a2a
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/routers/__init__.py
touch backend/app/services/__init__.py
```

**requirements.txt:**
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
google-generativeai==0.8.5
python-dotenv==1.0.1
pydantic-settings==2.7.1
httpx==0.28.1
websockets==14.1
```

---

### 1.2 Configuration (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///argus.db"
    
    # JWT
    jwt_secret: str = "argus-hackathon-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # Gemini
    google_api_key: str = ""
    gemini_eval_model: str = "gemini-2.0-flash"
    
    # Cards
    use_mock_cards: bool = True
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        env_prefix = "ARGUS_"

settings = Settings()
```

---

### 1.3 Database Setup (database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite needs this
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 1.4 Database Models

You're building 10 tables. Full schema with every column, type, constraint, and index is in **argus-data-spec.md Section 2**. Here's the summary:

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `users` | User accounts | Has many: profiles, payment_methods, transactions (denormalized) |
| `profiles` | Agent profiles (spending rule groups) | Belongs to user. Has many: spending_categories, connection_keys |
| `payment_methods` | Funding sources (method_type + detail JSON) | Belongs to user. Referenced by spending_categories (preferred funding per category) |
| `spending_categories` | Footwear, Electronics, Travel, General | Belongs to profile. Has many category_rules. Has one payment_method (optional) |
| `category_rules` | Immutable rule rows (new row per change, for Hedera audit) | Belongs to spending_category. Includes CUSTOM_RULE type for AI-evaluated rules. |
| `connection_keys` | API keys connecting agents to profiles | Belongs to profile. Key format: `argus_ck_` + 32 hex chars. Has optional `expires_at`. |
| `transactions` | Slim purchase requests (request_data JSON + status) | Belongs to user (denormalized) + connection_key. |
| `evaluations` | AI categorization + rules engine results + decision + risk_flags | One per transaction. Owns FK to transaction. |
| `human_approvals` | Approval lifecycle (only when HUMAN_NEEDED) | Has both transaction_id and evaluation_id. |
| `virtual_cards` | Issued single-use cards for approved purchases | One per approved transaction. Belongs to transaction + payment_method. |

**Transaction status lifecycle:**
```
PENDING_EVALUATION → AI_APPROVED / AI_DENIED / HUMAN_NEEDED
HUMAN_NEEDED → HUMAN_APPROVED / HUMAN_DENIED / HUMAN_TIMEOUT
AI_APPROVED / HUMAN_APPROVED → COMPLETED / EXPIRED / FAILED
```

**Evaluation decision values:** `APPROVE`, `DENY`, `HUMAN_NEEDED`

**Use UUID strings as primary keys:**
```python
import uuid
id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
```

---

### 1.5 API Endpoints — Complete List

**Authentication:**

| Method | Path | Auth | Called By | Purpose |
|--------|------|------|-----------|---------|
| POST | `/api/v1/auth/register` | None | Dashboard | Create user + default category + default rules |
| POST | `/api/v1/auth/login` | None | Dashboard | Returns JWT token |

**Core (Agent):**

| Method | Path | Auth | Called By | Purpose |
|--------|------|------|-----------|---------|
| POST | `/api/v1/evaluate` | Agent Key | ADK Plugin | **THE critical endpoint.** Evaluate purchase, return decision + virtual card |
| GET | `/api/v1/transactions/{id}/status` | Agent Key | ADK Plugin | Poll for human approval status |

**Dashboard:**

| Method | Path | Auth | Called By | Purpose |
|--------|------|------|-----------|---------|
| GET | `/api/v1/transactions` | JWT | Dashboard | List transactions (filterable, paginated) |
| GET | `/api/v1/transactions/{id}` | JWT | Dashboard | Full transaction detail |
| POST | `/api/v1/transactions/{id}/respond` | JWT | Dashboard | User approves or denies pending transaction |
| GET | `/api/v1/categories` | JWT | Dashboard | List categories with rules + spending totals |
| POST | `/api/v1/categories` | JWT | Dashboard | Create new category |
| PUT | `/api/v1/categories/{id}` | JWT | Dashboard | Edit category |
| GET | `/api/v1/connection-keys` | JWT | Dashboard | List connection keys (prefix only) |
| POST | `/api/v1/connection-keys` | JWT | Dashboard | Generate new key (returns full key ONCE) |
| DELETE | `/api/v1/connection-keys/{id}` | JWT | Dashboard | Revoke key |
| GET | `/api/v1/payment-methods` | JWT | Dashboard | List payment methods |
| POST | `/api/v1/payment-methods` | JWT | Dashboard | Add payment method |
| WS | `/ws/dashboard` | JWT (query param) | Dashboard | Real-time transaction updates |
| GET | `/health` | None | Anyone | Health check |

**Auth logic:** Look at the `Authorization: Bearer <token>` header. If token starts with `argus_ck_`, treat as connection key (look up in `connection_keys` table → resolve profile_id → user_id). Otherwise, decode as JWT.

---

### 1.6 POST /evaluate — The Critical Endpoint

This is the most important thing you build. Full request/response schemas are in **argus-data-spec.md Section 3.4**. Here's the processing pipeline:

```
STEP 1: Validate connection key
  - Look up key_value in connection_keys table
  - Confirm is_active = true and not expired (check expires_at)
  - Resolve profile_id → user_id
  - Update last_used_at
  - If invalid → 401

STEP 2: Extract merchant domain
  - Parse merchant_url (e.g., "https://www.amazon.com/checkout")
  - Extract domain: "amazon.com" (strip www.)

STEP 3: Create transaction row
  - Status: PENDING_EVALUATION
  - Store full request as request_data JSON: {product: {...}, chat_history: "..."}
  - Denormalize user_id onto the transaction
  - Return transaction_id

STEP 4: Load profile's spending categories
  - All categories for the resolved profile_id
  - Include name, description, keywords
  - Used to populate the Gemini prompt

STEP 5: GEMINI CALL 1 — Extract intent + category
  - Send ONLY chat_history + category list (NO product details in prompt)
  - Security: category comes from user intent, not agent claims
  - Returns: intent (want, budget, preferences) + category (name, confidence)
  - If fails: retry once → _mock_response() (default category, 0.90 confidence)

STEP 6: Match category to SpendingCategory row
  - Find spending_category WHERE name = gemini_response.category_name
    AND profile_id = resolved_profile
  - If no match: use the profile's default category (is_default=true)

STEP 7: Calculate spending totals
  - SUM price from transactions WHERE category matches
    AND status in (AI_APPROVED, HUMAN_APPROVED, COMPLETED)
  - Calculate daily, weekly, monthly totals

STEP 8: Run rules engine
  - Returns outcome (HARD_DENY / SOFT_FLAGS / ALL_PASS) + checks
  - CUSTOM_RULE recorded as pending_ai (evaluated by Call 2)
  - Rules engine no longer makes final decision

STEP 9: Assemble full report (intent + category + product + rules)

STEP 10: Decision routing
  IF HARD_DENY → decision = DENY, skip Gemini Call 2
  ELSE → proceed to step 11

STEP 11: GEMINI CALL 2 — Final decision
  - Send full report + CUSTOM_RULE prompts
  - Cross-checks: product vs intent, price vs budget, agent drift
  - Returns: decision, reasoning, confidence, risk_flags
  - If fails: conservative HUMAN_NEEDED

STEP 12: Apply guardrails
  - ALWAYS_REQUIRE_APPROVAL → force HUMAN_NEEDED
  - AUTO_APPROVE_UNDER fail → force HUMAN_NEEDED
  - Low AI confidence → force HUMAN_NEEDED

STEP 13: Execute decision
  IF APPROVE:
    - Determine payment method (category's payment_method_id,
      fallback to user's default)
    - Issue virtual card (call card_issuer service)
    - Update transaction: status = AI_APPROVED
    - Broadcast via WebSocket: TRANSACTION_DECIDED
    - Return full response with card details

  IF DENY:
    - Update transaction: status = AI_DENIED
    - Broadcast via WebSocket: TRANSACTION_DECIDED
    - Return response with reason, no card

  IF HUMAN_NEEDED:
    - Create human_approval row (with transaction_id + evaluation_id)
    - Update transaction: status = HUMAN_NEEDED
    - Broadcast via WebSocket: APPROVAL_REQUIRED
    - Return response with poll_url and timeout info
```

**Full request/response JSON examples are in argus-data-spec.md Section 3.4.** Copy them exactly.

---

### 1.7 Gemini Evaluator Service (gemini_evaluator.py)

```python
import google.generativeai as genai
import json

genai.configure(api_key=settings.google_api_key)

async def extract_intent_and_category(chat_history: str, categories: list) -> dict:
    """
    GEMINI CALL 1: Extract user intent and category from chat history.
    NO product details in prompt (security isolation).
    Returns: {intent: {want, budget, preferences, summary}, category: {name, confidence}}
    """

    model = genai.GenerativeModel(settings.gemini_eval_model)

    categories_json = json.dumps([{
        "name": c.name,
        "description": c.description,
        "is_default": c.is_default
    } for c in categories], indent=2)

    # Prompt sends ONLY chat_history + category list — no product details
    prompt = f"""..."""  # Full prompt from data spec Section 9.1 (Call 1)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        result = json.loads(response.text)
        return result
    except Exception as e:
        # Retry once
        try:
            response = model.generate_content(prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except:
            # Mock fallback — default category, high confidence, no risk flags
            return _mock_response(product_name="unknown", categories=categories)


async def make_final_decision(report: dict, custom_rules: list = None) -> dict:
    """
    GEMINI CALL 2: Given full report, cross-check intent vs product and decide.
    Returns: {decision, reasoning, confidence, risk_flags, intent_match, custom_rule_results}
    Only called when rules outcome is not HARD_DENY.
    """

    model = genai.GenerativeModel(settings.gemini_eval_model)

    # Send full report: intent + category + product + rules checks + custom rules
    prompt = f"""..."""  # Full prompt from data spec Section 9.2 (Call 2)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        result = json.loads(response.text)
        return result
    except Exception as e:
        # Retry once
        try:
            response = model.generate_content(prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except:
            # Conservative fallback — escalate to human
            return {
                "decision": "HUMAN_NEEDED",
                "reasoning": "Gemini was unavailable for final decision. Escalating to human.",
                "confidence": 0.0,
                "risk_flags": ["ai_evaluation_degraded"],
                "intent_match": 0.5,
                "custom_rule_results": []
            }


def _mock_response(product_name: str, categories: list) -> dict:
    """
    Stub response used when no GOOGLE_API_KEY is configured or Gemini fails.
    Returns the default category with high confidence and no risk flags so the
    rules engine runs cleanly against real seed data during local testing.
    """
    default_cat = next((c for c in categories if c.get("is_default")), None)
    category_name = default_cat["name"] if default_cat else (categories[0]["name"] if categories else "General")
    return {
        "category_name": category_name,
        "category_confidence": 0.90,
        "intent_match": 0.90,
        "intent_summary": f"[MOCK] {product_name} assigned to {category_name}. Gemini not configured.",
        "risk_flags": [],
        "reasoning": "[MOCK] Gemini unavailable. Returning stub response.",
        "custom_rule_results": []
    }
```

---

### 1.8 Rules Engine (rules_engine.py)

```python
def evaluate_rules(rules, price, merchant_domain, ledger_data):
    """
    Run each rule deterministically. Return list of check results
    and an outcome classification. CUSTOM_RULE is NOT evaluated here —
    it is recorded as pending_ai and evaluated by Gemini Call 2.

    rules: list of CategoryRule objects
    price: float
    merchant_domain: str
    ledger_data: dict with keys "daily", "weekly", "monthly" → float totals

    Returns: (outcome: str, checks: list[dict])
      outcome: "HARD_DENY" | "SOFT_FLAGS" | "ALL_PASS"
    """
    checks = []
    has_hard_fail = False
    has_soft_flag = False

    for rule in rules:
        if not rule.is_active:
            continue

        check = {
            "rule_id": rule.id,
            "rule_type": rule.rule_type,
        }

        if rule.rule_type == "MAX_PER_TRANSACTION":
            threshold = float(rule.value)
            passed = price <= threshold
            check.update({
                "threshold": threshold,
                "actual_value": price,
                "passed": passed,
                "detail": f"{price} {'<=' if passed else '>'} {threshold}"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "DAILY_LIMIT":
            threshold = float(rule.value)
            spent = ledger_data.get("daily", 0.0)
            total = spent + price
            passed = total <= threshold
            check.update({
                "threshold": threshold,
                "actual_value": total,
                "breakdown": {"previously_spent": spent, "this_transaction": price},
                "passed": passed,
                "detail": f"{spent} + {price} = {total} {'<=' if passed else '>'} {threshold}"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "WEEKLY_LIMIT":
            threshold = float(rule.value)
            spent = ledger_data.get("weekly", 0.0)
            total = spent + price
            passed = total <= threshold
            check.update({
                "threshold": threshold,
                "actual_value": total,
                "breakdown": {"previously_spent": spent, "this_transaction": price},
                "passed": passed,
                "detail": f"{spent} + {price} = {total} {'<=' if passed else '>'} {threshold}"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "MONTHLY_LIMIT":
            threshold = float(rule.value)
            spent = ledger_data.get("monthly", 0.0)
            total = spent + price
            passed = total <= threshold
            check.update({
                "threshold": threshold,
                "actual_value": total,
                "breakdown": {"previously_spent": spent, "this_transaction": price},
                "passed": passed,
                "detail": f"{spent} + {price} = {total} {'<=' if passed else '>'} {threshold}"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "AUTO_APPROVE_UNDER":
            threshold = float(rule.value)
            passed = price < threshold
            check.update({
                "threshold": threshold,
                "actual_value": price,
                "passed": passed,
                "detail": f"{price} {'<' if passed else '>='} {threshold}"
            })
            if not passed:
                has_soft_flag = True

        elif rule.rule_type == "MERCHANT_WHITELIST":
            whitelist = json.loads(rule.value)
            passed = merchant_domain in whitelist
            check.update({
                "merchant_domain": merchant_domain,
                "whitelist": whitelist,
                "passed": passed,
                "detail": f"{merchant_domain} {'is' if passed else 'is NOT'} in whitelist"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "MERCHANT_BLACKLIST":
            blacklist = json.loads(rule.value)
            passed = merchant_domain not in blacklist
            check.update({
                "merchant_domain": merchant_domain,
                "blacklist": blacklist,
                "passed": passed,
                "detail": f"{merchant_domain} {'is NOT' if passed else 'IS'} in blacklist"
            })
            if not passed:
                has_hard_fail = True

        elif rule.rule_type == "ALWAYS_REQUIRE_APPROVAL":
            if rule.value.lower() == "true":
                has_soft_flag = True
                check.update({
                    "passed": False,
                    "detail": "All purchases in this category require manual approval"
                })
            else:
                check.update({"passed": True, "detail": "Not enforced"})

        elif rule.rule_type == "BLOCK_CATEGORY":
            if rule.value.lower() == "true":
                has_hard_fail = True
                check.update({
                    "passed": False,
                    "detail": "This category is blocked"
                })
            else:
                check.update({"passed": True, "detail": "Not blocked"})

        elif rule.rule_type == "CUSTOM_RULE":
            # NOT evaluated here — recorded as pending_ai for Gemini Call 2
            has_soft_flag = True
            check.update({
                "passed": None,
                "status": "pending_ai",
                "detail": "Will be evaluated by Gemini Call 2",
                "prompt": rule.value
            })

        checks.append(check)

    # Outcome classification (not a final decision)
    if has_hard_fail:
        outcome = "HARD_DENY"
    elif has_soft_flag:
        outcome = "SOFT_FLAGS"
    else:
        outcome = "ALL_PASS"

    return outcome, checks
```

---

### 1.9 Mock Card Issuer (card_issuer.py)

```python
import hashlib
from datetime import datetime, timedelta

def issue_mock_card(transaction_id: str, price: float, merchant_domain: str):
    """Generate a deterministic mock virtual card."""
    seed = hashlib.sha256(transaction_id.encode()).hexdigest()
    
    card_number = "4532" + seed[:12]  # Visa-like prefix
    cvv = str(int(seed[:3], 16) % 900 + 100)  # 3-digit CVV (100-999)
    spend_limit = round(price * 1.15, 2)  # 15% buffer for tax/shipping
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    return {
        "card_number": card_number,
        "expiry_month": "03",
        "expiry_year": "2026",
        "cvv": cvv,
        "last_four": card_number[-4:],
        "spend_limit": spend_limit,
        "spend_limit_buffer": round(spend_limit - price, 2),
        "merchant_lock": merchant_domain,
        "external_card_id": f"mock_{transaction_id[:8]}",
        "expires_at": expires_at.isoformat() + "Z",
        "status": "ACTIVE"
    }
```

---

### 1.10 WebSocket Manager (websocket_manager.py)

```python
from fastapi import WebSocket
from typing import Dict
import json

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}  # user_id → websocket
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        self.connections.pop(user_id, None)
    
    async def send_to_user(self, user_id: str, message: dict):
        ws = self.connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except:
                self.disconnect(user_id)

ws_manager = WebSocketManager()
```

**WebSocket message types (server → client):**

```json
{"type": "TRANSACTION_CREATED", "data": {"transaction_id": "...", "product_name": "...", "price": 89.99, "merchant_name": "...", "status": "PENDING_EVALUATION"}}

{"type": "TRANSACTION_DECIDED", "data": {"transaction_id": "...", "decision": "APPROVE", "reason": "...", "category_name": "...", "virtual_card_last_four": "8847"}}

{"type": "APPROVAL_REQUIRED", "data": {"transaction_id": "...", "product_name": "...", "price": 578.00, "merchant_name": "...", "category_name": "...", "reason": "...", "timeout_seconds": 300}}

{"type": "VIRTUAL_CARD_USED", "data": {"transaction_id": "...", "card_last_four": "...", "amount": 97.42}}
```

---

### 1.11 FastAPI Main App (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Argus Core API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(evaluate_router, prefix="/api/v1", tags=["evaluate"])
app.include_router(transactions_router, prefix="/api/v1", tags=["transactions"])
app.include_router(categories_router, prefix="/api/v1", tags=["categories"])
app.include_router(profiles_router, prefix="/api/v1", tags=["profiles"])
app.include_router(connection_keys_router, prefix="/api/v1", tags=["connection-keys"])
app.include_router(payment_methods_router, prefix="/api/v1", tags=["payment-methods"])

# WebSocket
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Decode JWT from query param to get user_id
    user_id = decode_jwt(token)
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except:
        ws_manager.disconnect(user_id)

# A2A
app.mount("/.well-known", static_files_for_agent_card)
app.include_router(a2a_router, prefix="/a2a", tags=["a2a"])

# Health
@app.get("/health")
async def health():
    return {"status": "ok", "service": "argus-core"}

# Create tables + seed on startup
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
```

---

### 1.12 Seed Data (seed.py)

Full seed data is in **argus-data-spec.md Section 10**. Create these on startup if they don't exist:

- **Demo user:** email=demo@argus.dev, password=argus2026 (bcrypt hashed), name=Demo User
- **Payment methods:** Visa ending 4242 (default), Amex ending 1234
- **Categories:** Footwear, Electronics, Travel, General (default) — each with their rules as specified
- **Connection key:** `argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e`

Check if demo user exists first to avoid duplicate seed:
```python
def seed_demo_data():
    db = SessionLocal()
    if db.query(User).filter(User.email == "demo@argus.dev").first():
        return  # Already seeded
    # ... create all seed data
    db.commit()
    db.close()
```

---

## PART 2: ARGUS ADK PLUGIN

### 2.1 What the Plugin Does

The plugin is a Python class that hooks into the ADK agent's tool execution pipeline. Google ADK calls `before_tool_callback` before every tool the agent invokes. You check which tool is being called and either:

1. **Intercept `request_purchase`** → Call your API, handle response
2. **Intercept `type`/`input_text`** → Block unapproved card numbers (safety net)
3. **Let everything else pass** → Return None

### 2.2 Plugin Implementation

Full spec in **argus-data-spec.md Section 4**. Key structures:

**File: agent/argus_plugin/plugin.py**

```python
import httpx
import time
import re

class ArgusPlugin:
    """ADK Plugin that intercepts purchase requests and enforces payment authorization."""
    
    def __init__(
        self,
        argus_api_url: str = "http://localhost:8000/api/v1",
        connection_key: str = None,
        approval_timeout: int = 300,
        approval_poll_interval: int = 3,
    ):
        self.argus_api_url = argus_api_url
        self.connection_key = connection_key
        self.approval_timeout = approval_timeout
        self.approval_poll_interval = approval_poll_interval
        self.approved_cards = set()  # Track cards we've issued
    
    def before_tool_callback(self, tool, args, tool_context):
        """Called by ADK before every tool execution."""
        
        if tool.name == "request_purchase":
            return self._handle_purchase_request(args, tool_context)
        
        elif tool.name in ("type", "input_text", "enter_text"):
            return self._check_card_input(args)
        
        return None  # Allow all other tools
    
    def _handle_purchase_request(self, args, tool_context):
        """Intercept purchase request, call Argus API."""
        headers = {"Authorization": f"Bearer {self.connection_key}"}

        # Collect chat history from ADK session
        chat_history = self._extract_chat_history(tool_context)

        body = {
            "product": {
                "product_name": args.get("product_name"),
                "price": args.get("price"),
                "merchant_name": args.get("merchant_name"),
                "merchant_url": args.get("merchant_url"),
                "product_url": args.get("product_url"),
                "notes": args.get("notes"),
            },
            "chat_history": chat_history
        }

        response = httpx.post(
            f"{self.argus_api_url}/evaluate",
            json=body,
            headers=headers,
            timeout=30.0
        )
        data = response.json()
        
        if data["decision"] == "APPROVE":
            card = data["virtual_card"]
            self.approved_cards.add(card["card_number"])
            return {
                "status": "approved",
                "message": "Purchase approved by Argus.",
                "card_number": card["card_number"],
                "expiry_month": card["expiry_month"],
                "expiry_year": card["expiry_year"],
                "cvv": card["cvv"],
                "spend_limit": card["spend_limit"],
                "merchant_lock": card["merchant_lock"],
                "expires_at": card["expires_at"],
                "instructions": "Use ONLY these card details to complete checkout. Do not modify or substitute any values."
            }
        
        elif data["decision"] == "DENY":
            return {
                "status": "denied",
                "message": "Purchase denied by Argus.",
                "reason": data["reason"],
                "suggestion": "Try finding a cheaper alternative or a different merchant."
            }
        
        elif data["decision"] == "HUMAN_NEEDED":
            # Enter polling loop
            txn_id = data["transaction_id"]
            start = time.time()
            
            while time.time() - start < self.approval_timeout:
                time.sleep(self.approval_poll_interval)
                
                status_resp = httpx.get(
                    f"{self.argus_api_url}/transactions/{txn_id}/status",
                    headers=headers,
                    timeout=10.0
                )
                status_data = status_resp.json()
                
                if status_data["status"] == "HUMAN_APPROVED":
                    card = status_data["virtual_card"]
                    self.approved_cards.add(card["card_number"])
                    return {
                        "status": "approved",
                        "message": "User approved this purchase.",
                        "card_number": card["card_number"],
                        "expiry_month": card["expiry_month"],
                        "expiry_year": card["expiry_year"],
                        "cvv": card["cvv"],
                        "spend_limit": card["spend_limit"],
                        "merchant_lock": card["merchant_lock"],
                        "expires_at": card["expires_at"],
                        "instructions": "Use ONLY these card details."
                    }
                
                elif status_data["status"] in ("HUMAN_DENIED", "HUMAN_TIMEOUT"):
                    return {
                        "status": "denied",
                        "message": "User denied this purchase.",
                        "reason": status_data.get("reason", "User chose to deny.")
                    }
            
            # Timeout
            return {
                "status": "denied",
                "message": "Approval timed out.",
                "reason": "The user did not respond within the approval window."
            }
    
    def _check_card_input(self, args):
        """Safety net: block unapproved card numbers from being typed."""
        text = args.get("text", "")
        # Check for credit card pattern (13-19 digits)
        digits_only = re.sub(r'\D', '', text)
        if len(digits_only) >= 13 and len(digits_only) <= 19:
            if digits_only not in self.approved_cards:
                return {
                    "status": "blocked",
                    "message": "SECURITY: Cannot enter payment information without Argus authorization. Call request_purchase with the product details first.",
                    "action": "Call request_purchase before entering any card details."
                }
        return None  # Allow

    def _extract_chat_history(self, tool_context) -> str:
        """
        Extract conversation history from ADK session as plain text.
        Returns formatted string: "User: ...\nAgent: ...\n..."
        Only text messages, no attachments/screenshots.
        """
        # TODO: Implement based on ADK session API
        # Access tool_context.session or equivalent to get message history
        # Format each message as "Role: content\n"
        return ""
```

**File: agent/argus_plugin/request_purchase.py**

```python
def request_purchase(
    product_name: str,
    price: float,
    merchant_name: str,
    merchant_url: str,
    product_url: str = None,
    notes: str = None
) -> dict:
    """Request authorization to purchase a product through Argus.

    You MUST call this tool before entering any payment information.
    This tool verifies the purchase against user spending rules and
    returns payment card details if approved.

    Args:
        product_name: The exact name of the product being purchased.
        price: The exact price shown at checkout, in USD.
        merchant_name: The name of the store/merchant.
        merchant_url: The full URL of the checkout page.
        product_url: The URL of the product detail page (optional).
        notes: Any additional context about the purchase, such as
               color, size, or reason for selection (optional).

    Returns:
        dict with 'status' ('approved', 'denied', or 'human_needed').
        If approved: includes card_number, expiry_month, expiry_year, cvv.
        If denied: includes reason and suggestion.
    """
    # This function body is intercepted by the Argus Plugin.
    # It never actually executes.
    return {"status": "error", "message": "Argus plugin not loaded"}
```

**IMPORTANT NOTE ON ADK PLUGIN API:** The exact way to register a plugin with ADK may depend on which ADK version we're using. Check the ADK docs for how `before_tool_callback` gets registered. The spec above uses `BasePlugin` but the actual ADK API might differ. Prem will set up the agent runner and can help you figure out the exact hook mechanism.

---

## PART 3: A2A ENDPOINT

### 3.1 What It Is

Google's Agent-to-Agent protocol lets any A2A-compatible agent discover Argus and use it. We implement:

1. **Agent Card** at `/.well-known/agent.json` — describes Argus capabilities
2. **Task handler** at `/a2a` — receives JSON-RPC requests, translates to our `/evaluate` flow

### 3.2 Agent Card

**File: backend/a2a/agent_card.py** (or serve as static JSON)

```json
{
  "name": "Argus Payment Guardian",
  "description": "AI agent payment authorization system. Evaluates purchase requests against user-defined spending rules, issues scoped virtual cards for approved purchases.",
  "url": "http://localhost:8000/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "evaluate_purchase",
      "name": "Evaluate Purchase",
      "description": "Submit a purchase request for authorization. Returns approval with virtual card details, denial with reason, or escalation to human review.",
      "inputModes": ["application/json"],
      "outputModes": ["application/json"]
    }
  ],
  "authentication": {
    "schemes": ["bearer"]
  }
}
```

### 3.3 Task Handler

**File: backend/a2a/handler.py**

The `/a2a` endpoint receives JSON-RPC 2.0 requests with method `tasks/send`. Extract the purchase details from the task message, call our existing evaluate logic, return the result.

```python
@router.post("/a2a")
async def handle_a2a(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    
    # JSON-RPC 2.0 format
    method = body.get("method")
    if method != "tasks/send":
        return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}}
    
    params = body.get("params", {})
    message = params.get("message", {})
    
    # Extract purchase details from the A2A task
    # (the external agent sends product info in the message)
    # Map to our evaluate request format
    # Call the same evaluate logic
    # Return result in A2A task response format
    
    return {
        "jsonrpc": "2.0",
        "result": {
            "id": params.get("id", str(uuid.uuid4())),
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "data", "data": result}]}]
        }
    }
```

**Time-box this to 3 hours max.** If it's not working cleanly, skip it — we mention it in the pitch with the architecture diagram showing the endpoint exists.

---

## PART 4: DEPLOYMENT

### 4.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Create data directory for SQLite
RUN mkdir -p /data

ENV ARGUS_DATABASE_URL=sqlite:////data/argus.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 docker-compose.yml

```yaml
version: "3.8"
services:
  argus-api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - argus-data:/data
    env_file:
      - .env
    restart: unless-stopped

volumes:
  argus-data:
```

### 4.3 Deploy Backend to Dockploy

1. Push to GitHub
2. In Dockploy, create new project → connect GitHub repo
3. Set build context to root, Dockerfile path to `backend/Dockerfile`
4. Add environment variables
5. Mount persistent volume at `/data`
6. Deploy

### 4.4 Vercel Frontend Config

Prem handles the frontend deploy, but you may need to help with:
- Set `VITE_API_URL` environment variable to the Dockploy backend URL
- Set `VITE_WS_URL` to the WebSocket URL (change ws:// to wss:// for production)
- CORS: Add the Vercel domain to `ARGUS_CORS_ORIGINS`

---

## PART 5: DOCUMENTATION

### 5.1 README.md

Write setup instructions:
- Prerequisites (Python 3.11+, Node.js 18+, npm)
- Clone repo, install deps, set env vars
- `python backend/seed.py` to populate demo data
- `uvicorn backend.app.main:app --reload` to start API
- `cd frontend && npm install && npm run dev` to start dashboard
- Demo credentials: demo@argus.dev / argus2026

### 5.2 ARCHITECTURE.md

Write for judges evaluating Code Quality:
- System architecture diagram (text-based)
- Component descriptions
- Authentication flow
- Evaluate pipeline description
- A2A protocol integration
- Database schema overview
- Deployment architecture

---

## Build Order (What to Build First)

1. **Database models + seed** → Foundation everything depends on
2. **Auth endpoints** → Login/register so Prem can start building dashboard auth
3. **POST /evaluate** → THE critical endpoint. Get this working even with a simplified rules engine first, then refine
4. **GET /transactions** → So Prem can display the transaction feed
5. **WebSocket** → So Prem can get real-time updates
6. **GET /categories** → Dashboard categories page
7. **POST /transactions/{id}/respond endpoint** → Dashboard approval flow
8. **ADK Plugin** → So Prem can test the full agent flow
9. **Other CRUD endpoints** → Connection keys, payment methods
10. **A2A endpoint** → Innovation differentiator
11. **Docker + deploy** → Get it live
12. **README + ARCHITECTURE.md** → Code quality score

---

## Integration Checkpoints with Prem

**Checkpoint 1 (Hour ~2):** Auth working. Prem can call POST /login from React and get a JWT.

**Checkpoint 2 (Hour ~4):** GET /transactions returns seeded data. WebSocket sends test messages. Prem can display transactions in the dashboard.

**Checkpoint 3 (Hour ~6):** POST /evaluate fully working. Plugin built. Prem connects agent → runs first end-to-end test.

**Checkpoint 4 (Hour ~8):** POST /respond working. WebSocket broadcasts approvals. Prem tests full human-in-the-loop flow.

**Checkpoint 5 (Hour ~10):** Everything deployed. Prem records demo video.

---

## Reference

- **argus-data-spec.md** — Your source of truth for ALL schemas, contracts, and interfaces
- **argus-project-overview.md** — High-level project context
- **argus-prem-guide.md** — What Prem is building (so you know what he needs from you)
