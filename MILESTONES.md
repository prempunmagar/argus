# ARGUS — Build Milestones & Progress Tracker

> **Last Updated:** 2026-02-21 (Milestone 2 complete)
> **Role:** Backend Builder (Core API, ADK Plugin, A2A, Deploy, Docs)
> **Status:** COMPLETE — Milestone 2. Auth endpoints tested and working. Next: Milestone 3 (/evaluate)

> **How to use this file:** Check off tasks as they're completed. Anyone picking this up mid-build can see exactly where things stand. Update the "Last Updated" date and any notes when you make progress.

---

## Legend

- [ ] Not started
- [x] Completed
- [~] In progress / partially done
- [!] Blocked / needs attention

---

## Milestone 1: Project Scaffolding & Database Foundation

**Goal:** Create project structure, install dependencies, build all 9 database models, seed demo data.
**Unblocks:** Everything else.

### Tasks

- [x] Create directory structure (`backend/app/models/`, `schemas/`, `routers/`, `services/`, `a2a/`, `agent/argus_plugin/`)
- [x] Create `backend/requirements.txt` with all dependencies
- [x] Create `backend/.env.example` with all env vars
- [x] Create `.env` file with placeholder values (GOOGLE_API_KEY placeholder)
- [x] Build `backend/app/config.py` — Pydantic Settings
- [x] Build `backend/app/database.py` — SQLAlchemy engine, SessionLocal, Base, get_db
- [x] Build all 9 database models:
  - [x] `models/user.py` — users table
  - [x] `models/payment_method.py` — payment_methods table
  - [x] `models/spending_category.py` — spending_categories table
  - [x] `models/category_rule.py` — category_rules table
  - [x] `models/profile.py` — profiles table (replaced agent_keys)
  - [x] `models/connection_key.py` — connection_keys table (replaced agent_keys)
  - [x] `models/transaction.py` — transactions table (the big one)
  - [x] `models/virtual_card.py` — virtual_cards table
  - [x] `models/spending_ledger.py` — spending_ledger table
  - [x] `models/__init__.py` — import all models
- [ ] Build `backend/seed.py` — seed demo user, payment methods, categories, rules, demo profile + connection key
- [ ] Verify: database creates all tables on startup
- [ ] Verify: seed data populates correctly (demo@argus.dev, 4 categories, rules, agent key)

**Notes:**
- UUID strings as primary keys: `id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`
- SQLite needs `check_same_thread=False`
- Seed data IDs are deterministic (e.g., `usr_demo_001`, `pm_visa_001`) per data spec Section 10
- All column definitions, types, and constraints are in `argus-data-spec.md` Section 2
- **Design Decision:** `transactions.virtual_card_id` has NO ForeignKey constraint. VirtualCard and Transaction reference each other (circular dependency), and SQLite can't handle deferred FK constraints. The FK is kept on VirtualCard's side (`transaction_id → transactions.id`), and Transaction stores `virtual_card_id` as a plain string. The link is enforced in application code.

---

## Milestone 2: Auth Endpoints

**Goal:** Login and register working. Prem can get a JWT from the API.
**Unblocks:** Prem's dashboard auth, all JWT-protected endpoints.
**Integration Checkpoint:** Hour ~2 — Prem can POST /login and get a JWT.

### Tasks

- [x] Build auth schemas (`schemas/auth.py`) — LoginRequest, RegisterRequest, AuthResponse
- [x] Build auth helper functions (`services/auth.py`) — create_jwt, decode_jwt, hash_password, verify_password
- [x] Build unified auth dependency (`dependencies.py`) — detect agent key vs JWT from Bearer token
- [x] Build `routers/auth.py`:
  - [x] `POST /api/v1/auth/register` — create user + default "General" category + default rules, return JWT
  - [x] `POST /api/v1/auth/login` — verify credentials, return JWT
- [x] Build `routers/health.py` — `GET /health`
- [x] Build `backend/app/main.py` — FastAPI app with CORS, router includes, startup event (create tables)
- [x] Verify: can register a new user and get JWT back
- [x] Verify: can login with registered user and get JWT back
- [x] Verify: duplicate email returns 409
- [x] Verify: wrong password returns 401
- [x] Verify: health endpoint returns `{"status": "ok", "service": "argus-core"}`

**Notes:**
- JWT payload: `{"sub": user_id, "email": email, "exp": expiry}`
- Register side effects: creates User + default SpendingCategory ("General") + 3 default rules (MAX_PER_TRANSACTION: 500, AUTO_APPROVE_UNDER: 50, DAILY_LIMIT: 1000)
- Auth logic: if token starts with `argus_ak_`, look up connection_keys table → resolve profile → user; otherwise decode as JWT
- CORS origins: `http://localhost:3000,http://localhost:5173`
- Pinned `bcrypt==4.0.1` in requirements.txt to fix passlib compatibility issue
- Removed `account_type` field from User model and all spec docs (was PERSONAL/INSTITUTIONAL, not needed for MVP)
- Demo user login not yet testable — seed.py still deferred until user finishes model changes

---

## Milestone 3: The /evaluate Endpoint (CRITICAL)

**Goal:** The 10-step evaluation pipeline fully working. Agent can submit purchase, get APPROVE/DENY/REQUIRE_APPROVAL.
**Unblocks:** End-to-end flow, ADK plugin, demo scenarios.
**This is the most important thing we build.**

### Tasks

- [ ] Build evaluate schemas (`schemas/evaluate.py`) — EvaluateRequest, EvaluateResponse
- [ ] Build Gemini evaluator service (`services/gemini_evaluator.py`):
  - [ ] Gemini API call with prompt from data spec Section 9.1
  - [ ] JSON response parsing (category_name, confidence, intent_match, risk_flags, reasoning)
  - [ ] Retry logic (retry once on failure)
  - [ ] Keyword-based fallback when Gemini unavailable
- [ ] Build rules engine service (`services/rules_engine.py`):
  - [ ] Evaluate all 9 rule types (MAX_PER_TRANSACTION, DAILY_LIMIT, WEEKLY_LIMIT, MONTHLY_LIMIT, AUTO_APPROVE_UNDER, MERCHANT_WHITELIST, MERCHANT_BLACKLIST, ALWAYS_REQUIRE_APPROVAL, BLOCK_CATEGORY)
  - [ ] Record each check result as JSON
  - [ ] Decision priority logic: BLOCK_CATEGORY > hard-fails > ALWAYS_REQUIRE_APPROVAL > AUTO_APPROVE_UNDER > Gemini risk flags > APPROVE
- [ ] Build mock card issuer service (`services/card_issuer.py`):
  - [ ] Deterministic card generation from transaction_id hash
  - [ ] 15% spend limit buffer, 30-min expiry, merchant lock
- [ ] Build WebSocket manager service (`services/websocket_manager.py`):
  - [ ] Connection tracking by user_id
  - [ ] send_to_user method
- [ ] Build `routers/evaluate.py` — the 10-step pipeline:
  - [ ] Step 1: Validate agent key, resolve user_id
  - [ ] Step 2: Extract merchant domain from merchant_url
  - [ ] Step 3: Create transaction row (PENDING_EVALUATION)
  - [ ] Step 4: Load user's spending categories
  - [ ] Step 5: Call Gemini for categorization + risk
  - [ ] Step 6: Match category from Gemini response
  - [ ] Step 7: Load rules for matched category
  - [ ] Step 8: Run rules engine, record results
  - [ ] Step 9: Make decision (APPROVE / DENY / REQUIRE_APPROVAL)
  - [ ] Step 10: Execute decision (issue card if approved, update ledger, broadcast WebSocket)
- [ ] Build spending ledger query helpers (get daily/weekly/monthly totals)
- [ ] Build spending ledger upsert (update totals on approval)
- [ ] Verify: POST /evaluate with demo agent key → APPROVE for cheap shoes on amazon.com
- [ ] Verify: POST /evaluate → DENY when price exceeds limits
- [ ] Verify: POST /evaluate → REQUIRE_APPROVAL for Travel category

**Notes:**
- Gemini prompt is in `argus-data-spec.md` Section 9.1 — copy it exactly
- If no GOOGLE_API_KEY, keyword fallback should work as default path
- Merchant domain extraction: parse URL, strip `www.` prefix
- Response shapes for all 3 decision types are in data spec Section 3.4

---

## Milestone 4: Transaction Endpoints

**Goal:** Dashboard can list transactions, view details, poll status.
**Unblocks:** Prem's transaction feed page, plugin polling.
**Integration Checkpoint:** Hour ~4 — GET /transactions returns data.

### Tasks

- [ ] Build transaction schemas (`schemas/transaction.py`) — TransactionListResponse, TransactionDetail
- [ ] Build `routers/transactions.py`:
  - [ ] `GET /api/v1/transactions` — list with filters (status, category_id), pagination (limit, offset), sorting
  - [ ] `GET /api/v1/transactions/{id}` — full transaction detail
  - [ ] `GET /api/v1/transactions/{id}/status` — for plugin polling (agent key auth)
- [ ] Verify: GET /transactions returns seeded/created transactions
- [ ] Verify: filtering by status works
- [ ] Verify: GET /transactions/{id}/status returns correct status + virtual card when approved

**Notes:**
- Transaction list response includes virtual_card_last_four and virtual_card_status (denormalized)
- Status endpoint is called by the ADK plugin during polling — must use agent key auth
- Default sort: created_at descending

---

## Milestone 5: WebSocket Real-time Updates

**Goal:** Dashboard receives live transaction updates.
**Unblocks:** Prem's real-time transaction feed.
**Integration Checkpoint:** Hour ~4 — WebSocket sends test messages.

### Tasks

- [ ] Implement WebSocket endpoint in main.py (`/ws/dashboard?token=JWT`)
- [ ] JWT validation from query parameter
- [ ] Connection lifecycle (connect, keep-alive, disconnect)
- [ ] Wire WebSocket broadcasts into /evaluate pipeline (TRANSACTION_CREATED, TRANSACTION_DECIDED, APPROVAL_REQUIRED)
- [ ] Verify: connect via WebSocket with valid JWT
- [ ] Verify: POST /evaluate triggers WebSocket message to connected dashboard

**Notes:**
- 4 message types: TRANSACTION_CREATED, TRANSACTION_DECIDED, APPROVAL_REQUIRED, VIRTUAL_CARD_USED
- Message shapes defined in data spec Section 3.17
- Token passed as query param, not header (WebSocket limitation)

---

## Milestone 6: Categories Endpoints

**Goal:** Dashboard can display and manage spending categories and rules.
**Unblocks:** Prem's categories page.

### Tasks

- [ ] Build category schemas (`schemas/category.py`) — CategoryResponse, CreateCategoryRequest, UpdateCategoryRequest
- [ ] Build `routers/categories.py`:
  - [ ] `GET /api/v1/categories` — list all categories with rules + spending totals
  - [ ] `POST /api/v1/categories` — create new category with rules
  - [ ] `PUT /api/v1/categories/{id}` — update category (partial updates OK)
- [ ] Include spending_today, spending_this_week, spending_this_month from ledger
- [ ] Verify: GET /categories returns all 4 demo categories with rules and spending totals

**Notes:**
- Categories response includes nested rules array and spending totals
- POST creates category + associated rules in one request
- PUT supports partial updates — only update fields that are provided

---

## Milestone 7: Approve/Deny Endpoints

**Goal:** User can approve or deny pending transactions from dashboard.
**Unblocks:** Full human-in-the-loop flow, demo Scenario 3 (Travel).
**Integration Checkpoint:** Hour ~8 — Approve/deny working, WebSocket broadcasts approvals.

### Tasks

- [ ] Build approval schemas (`schemas/approval.py`) — ApproveRequest, DenyRequest, ApprovalResponse
- [ ] Build `routers/approvals.py`:
  - [ ] `POST /api/v1/transactions/{id}/approve` — approve pending transaction
    - [ ] Validate transaction is PENDING_APPROVAL and belongs to user
    - [ ] Issue virtual card
    - [ ] Update spending ledger
    - [ ] Update transaction (status=APPROVED, approved_by=USER_APPROVE)
    - [ ] Broadcast WebSocket update
  - [ ] `POST /api/v1/transactions/{id}/deny` — deny pending transaction
    - [ ] Validate transaction is PENDING_APPROVAL and belongs to user
    - [ ] Update transaction (status=DENIED, approved_by=USER_DENY)
    - [ ] Broadcast WebSocket update
- [ ] Verify: approve a pending transaction → card issued, status updated
- [ ] Verify: deny a pending transaction → status updated, reason stored
- [ ] Verify: plugin polling picks up the approval/denial

**Notes:**
- Only transactions with status PENDING_APPROVAL can be approved/denied
- Approval issues a virtual card (same card_issuer logic as auto-approve)
- Both endpoints accept optional `note` field
- WebSocket broadcasts so plugin's poll loop picks up the change

---

## Milestone 8: ADK Plugin

**Goal:** Plugin intercepts request_purchase, calls API, handles all 3 response types.
**Unblocks:** End-to-end agent flow, Prem's agent testing.
**Integration Checkpoint:** Hour ~6 — First end-to-end test.

### Tasks

- [ ] Build `agent/argus_plugin/__init__.py`
- [ ] Build `agent/argus_plugin/plugin.py` — ArgusPlugin class:
  - [ ] `before_tool_callback` — detect tool name, route to handler
  - [ ] `_handle_purchase_request` — POST to /evaluate, handle 3 response types
  - [ ] `_check_card_input` — safety net for unapproved card numbers
  - [ ] Polling loop for REQUIRE_APPROVAL (configurable timeout + interval)
- [ ] Build `agent/argus_plugin/request_purchase.py` — tool definition (function signature + docstring)
- [ ] Build `agent/argus_plugin/session_store.py` — track approved card numbers
- [ ] Verify: plugin intercepts request_purchase and calls /evaluate
- [ ] Verify: approved cards are tracked and allowed through type() safety net
- [ ] Verify: unapproved card numbers are blocked

**Notes:**
- Plugin uses httpx for HTTP calls to the API
- Polling: every 3 seconds, up to 300 seconds (configurable)
- The exact ADK plugin API may differ from spec — check ADK docs for `before_tool_callback` registration
- Card safety net: regex for 13-19 digit sequences in type() calls

---

## Milestone 9: CRUD Endpoints (Agent Keys, Payment Methods)

**Goal:** Dashboard can manage agent keys and payment methods.
**Unblocks:** Prem's agent keys page, payment methods page.

### Tasks

- [ ] Build `routers/agents.py`:
  - [ ] `GET /api/v1/profiles` — list profiles
  - [ ] `POST /api/v1/profiles` — create new profile
  - [ ] `GET /api/v1/profiles/{id}/keys` — list connection keys (prefix only, never full key)
  - [ ] `POST /api/v1/profiles/{id}/keys` — generate new connection key (return full key ONCE)
  - [ ] `DELETE /api/v1/profiles/{id}/keys/{key_id}` — revoke key (soft delete: is_active=false)
- [ ] Build `routers/payment_methods.py`:
  - [ ] `GET /api/v1/payment-methods` — list all
  - [ ] `POST /api/v1/payment-methods` — add new
- [ ] Verify: can create agent key, see it listed (prefix only), revoke it
- [ ] Verify: can add payment method and see it listed

**Notes:**
- Connection key format: `argus_ak_` + sha256(id + profile_id + created_at)[:32]
- key_prefix: first 12 chars of key_value (e.g., "argus_ak_7f3b")
- Full key_value only returned on POST (creation) — subsequent GETs show prefix only
- DELETE is a soft-delete (is_active = false), not a hard delete

---

## Milestone 10: A2A Endpoint

**Goal:** Agent-to-Agent protocol endpoint for discoverability.
**Time-boxed:** 3 hours max. If not working cleanly, skip — mention in pitch only.

### Tasks

- [ ] Build `backend/a2a/agent_card.py` — Agent Card JSON
- [ ] Serve Agent Card at `/.well-known/agent.json`
- [ ] Build `backend/a2a/handler.py` — JSON-RPC 2.0 handler
  - [ ] Parse `tasks/send` method
  - [ ] Extract purchase details from A2A task message
  - [ ] Call existing evaluate logic
  - [ ] Return result in A2A task response format
- [ ] Verify: GET /.well-known/agent.json returns valid Agent Card
- [ ] Verify: POST /a2a with tasks/send processes a purchase evaluation

**Notes:**
- A2A is a differentiator for Innovation judging, not core functionality
- If time is running out, skip this and mention it in the pitch only
- Agent Card schema defined in data spec Section 3 (A2A section of teammate guide Part 3)

---

## Milestone 11: Docker & Deployment

**Goal:** Backend running in Docker, deployed to Dockploy. Frontend deployed to Vercel.

### Tasks

- [ ] Create `backend/Dockerfile`
- [ ] Create `docker-compose.yml` with persistent volume
- [ ] Test: `docker-compose up` starts the API correctly
- [ ] Test: API is accessible, seed data loads, endpoints work
- [ ] Deploy to Dockploy:
  - [ ] Push to GitHub
  - [ ] Create project in Dockploy
  - [ ] Set environment variables
  - [ ] Mount persistent volume at /data
  - [ ] Deploy and verify
- [ ] Update CORS origins to include deployed frontend URL
- [ ] Help Prem with Vercel config if needed (VITE_API_URL, VITE_WS_URL)

**Notes:**
- SQLite database file goes on persistent volume: `/data/argus.db`
- CORS must include both localhost origins AND deployed frontend origin
- WebSocket URL changes from `ws://` to `wss://` in production

---

## Milestone 12: Documentation

**Goal:** README.md and ARCHITECTURE.md for Code Quality judging score.

### Tasks

- [ ] Create `README.md`:
  - [ ] Project overview (what Argus is)
  - [ ] Prerequisites (Python 3.11+, Node.js 18+)
  - [ ] Setup instructions (clone, install, env vars, seed, run)
  - [ ] Demo credentials (demo@argus.dev / argus2026)
  - [ ] API documentation summary
  - [ ] Architecture overview
- [ ] Create `ARCHITECTURE.md`:
  - [ ] System architecture diagram (text-based)
  - [ ] Component descriptions
  - [ ] Authentication flow (JWT + agent keys)
  - [ ] Evaluate pipeline description (10 steps)
  - [ ] A2A protocol integration
  - [ ] Database schema overview
  - [ ] Deployment architecture

**Notes:**
- Judges evaluate videos over 2 weeks — they do NOT clone repos
- But Code Quality is a judging criterion, so clean docs matter
- Keep it concise but professional

---

## Quick Reference

### Key Files to Reference During Build
| What | Where |
|------|-------|
| All API contracts & response shapes | `argus-data-spec (1).md` Section 3 |
| Database schemas (every column) | `argus-data-spec (1).md` Section 2 |
| Gemini prompt (copy exactly) | `argus-data-spec (1).md` Section 9.1 |
| Seed data (demo user, categories, rules) | `argus-data-spec (1).md` Section 10 |
| Code snippets for every component | `argus-kes-guide.md` |
| Build order & integration checkpoints | `CLAUDE.md` |

### Demo Credentials
- **Email:** demo@argus.dev
- **Password:** argus2026
- **Agent Key:** `argus_ak_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e`

### Ports
- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000` or `http://localhost:5173`
- ADK Dev UI: `http://localhost:8080`

### Environment Variables Needed
```bash
ARGUS_DATABASE_URL=sqlite:///argus.db
ARGUS_JWT_SECRET=argus-hackathon-secret-change-in-prod
ARGUS_JWT_EXPIRY_HOURS=24
GOOGLE_API_KEY=<placeholder-get-from-team>
GEMINI_EVAL_MODEL=gemini-2.0-flash
USE_MOCK_CARDS=true
ARGUS_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-02-20 | Created milestone tracker | Backend Builder |
| 2026-02-20 | Completed: directory structure, requirements.txt, .env files, config.py, database.py | Backend Builder |
| 2026-02-20 | Completed: 6 of 8 models (User, PaymentMethod, SpendingCategory, CategoryRule, AgentKey, Transaction) | Backend Builder |
| 2026-02-20 | Design decision: removed FK from transactions.virtual_card_id due to SQLite circular dependency | Backend Builder |
| 2026-02-20 | Completed: VirtualCard + SpendingLedger models, models/__init__.py | Backend Builder |
| 2026-02-20 | Completed: auth schemas, auth service (JWT + bcrypt), auth dependency | Backend Builder |
| 2026-02-20 | Fix: pinned bcrypt==4.0.1 for passlib compatibility | Backend Builder |
| 2026-02-20 | Removed account_type from User model + all spec docs | Backend Builder |
| 2026-02-21 | Completed: auth router (register + login), health router, main.py | Backend Builder |
| 2026-02-21 | Verified: all auth endpoints tested — register, login, duplicate email 409, wrong password 401, health check | Backend Builder |
| 2026-02-21 | Schema change: replaced agent_keys table with profiles + connection_keys. Updated transaction.py (agent_key_id → connection_key_id), models/__init__.py, dependencies.py, all spec docs | Backend Builder |

