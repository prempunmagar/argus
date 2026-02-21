# CLAUDE.md — Argus Project Context

## What Is This Project?

Argus is an AI agent payment authorization system being built for the LIVE AI Ivy Plus Hackathon 2026. It intercepts AI shopping agent purchases, evaluates them against user-defined spending rules using Gemini AI, and issues scoped virtual cards for approved transactions.

## Who Am I (The Developer Using This CLI)?

I am the **Backend Builder** — I own the backend API, ADK plugin, A2A endpoint, database, and deployment. See `argus-teammate-guide.md` for my full build guide.

## My Scope — What I Build

1. **Argus Core API** — FastAPI, all endpoints, all services, database (in `backend/`)
2. **Argus ADK Plugin** — `before_tool_callback` that intercepts agent purchase calls (in `agent/argus_plugin/`)
3. **A2A Endpoint** — Google's Agent-to-Agent protocol for discoverability (in `backend/a2a/`)
4. **Database** — SQLAlchemy models, seed data
5. **Deployment** — Docker, Dockploy (backend), Vercel config (frontend)
6. **Documentation** — README.md, ARCHITECTURE.md

## What I Do NOT Touch

- `frontend/` — Prem builds the React dashboard
- `agent/shopping_agent/` — Prem builds the shopping agent
- `agent/run_agent.py` — Prem's agent runner
- Pitch materials

# Build Rules (FOLLOW THESE)

1. **Small steps, manual verification.** Each milestone is broken into small steps. Implement ONE step at a time. Each step must produce code the developer can review and manually test. Stop after each step and wait for the developer to confirm before proceeding.
2. **Consult on test failures.** If a test or verification fails 2-3 times, STOP and explain the problem to the developer. Do not silently keep trying fixes. The developer wants to be involved and understand what's going wrong.
3. **Update MILESTONES.md as we go.** After completing each step, update `MILESTONES.md` — check off completed tasks, add any design decisions to the Notes section, and add an entry to the Change Log. Anyone picking up this project mid-build should be able to read MILESTONES.md and know exactly where things stand.
4. **Update ALL context files when we make changes.** Whenever we add, remove, or rename a field, table, endpoint, or any structural element: do a **project-wide search** (grep the entire Argus directory) for every reference to the changed item. Update ALL files that mention it — code files, spec docs (argus-data-spec, argus-kes-guide, argus-project-overview), CLAUDE.md, MILESTONES.md, and any other context or rules files. Never assume only one file is affected. Docs must always stay in sync with reality.

## Key Reference Documents (READ THESE)

- **`argus-data-spec.md`** — THE source of truth for all API contracts, database schemas, request/response shapes, WebSocket messages, Gemini prompts, seed data, and rules engine logic. Reference this for EVERY endpoint and integration point.
- **`argus-teammate-guide.md`** — My detailed build guide with code snippets for every component I build.
- **`argus-project-overview.md`** — High-level architecture, core flow, tech stack, demo scenarios.
- **`argus-prem-guide.md`** — What Prem is building. Useful for understanding what the dashboard expects from my API.

## Tech Stack (My Parts)

- **API Framework:** FastAPI (Python 3.11+)
- **Database:** SQLite + SQLAlchemy ORM
- **Auth:** JWT (python-jose + bcrypt) for dashboard, static agent keys for agents
- **AI Evaluation:** Google Gemini 2.0 Flash (google-generativeai SDK)
- **Virtual Cards:** Mock card issuer (deterministic, no external dependency)
- **Real-time:** FastAPI native WebSocket
- **HTTP Client:** httpx (for plugin → API calls)
- **Deployment:** Docker + Dockploy

## Project Structure

```
argus/
├── backend/                    # [MY DOMAIN]
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app, CORS, startup, WebSocket
│   │   ├── config.py           # Pydantic Settings from env
│   │   ├── database.py         # SQLAlchemy engine, session, Base
│   │   ├── models/             # SQLAlchemy ORM models (10 tables)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── profile.py
│   │   │   ├── payment_method.py
│   │   │   ├── spending_category.py
│   │   │   ├── category_rule.py
│   │   │   ├── connection_key.py
│   │   │   ├── transaction.py
│   │   │   ├── evaluation.py
│   │   │   ├── human_approval.py
│   │   │   └── virtual_card.py
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── evaluate.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   └── approval.py
│   │   ├── routers/            # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── evaluate.py
│   │   │   ├── transactions.py
│   │   │   ├── categories.py
│   │   │   ├── approvals.py
│   │   │   ├── agents.py
│   │   │   ├── payment_methods.py
│   │   │   └── health.py
│   │   └── services/           # Business logic
│   │       ├── __init__.py
│   │       ├── gemini_evaluator.py
│   │       ├── rules_engine.py
│   │       ├── card_issuer.py
│   │       └── websocket_manager.py
│   ├── a2a/                    # A2A protocol
│   │   ├── agent_card.py
│   │   └── handler.py
│   ├── seed.py                 # Database seeding
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── agent/
│   └── argus_plugin/           # [MY DOMAIN]
│       ├── __init__.py
│       ├── plugin.py           # ArgusPlugin with before_tool_callback
│       ├── request_purchase.py # Tool definition (intercepted by plugin)
│       └── session_store.py
├── argus-data-spec.md
├── argus-teammate-guide.md
├── argus-project-overview.md
├── argus-prem-guide.md
└── CLAUDE.md                   # This file
```

## Build Order (Follow This Sequence — Priority Order)

1. **Database models + seed** — Foundation everything depends on. 10 tables defined in argus-data-spec.md Section 2.
2. **Auth endpoints** — `POST /auth/login` and `/auth/register` so Prem can start building dashboard auth.
3. **POST /evaluate** — THE critical endpoint. Full 10-step pipeline in argus-teammate-guide.md Section 1.6 and argus-data-spec.md Section 3.4. Get this working even with a simplified rules engine first, then refine.
4. **GET /transactions** — So Prem can display the transaction feed.
5. **WebSocket** — `/ws/dashboard` so Prem can get real-time updates.
6. **GET /categories** — Dashboard categories page.
7. **Approve/deny endpoints** — `POST /transactions/{id}/approve` and `/deny`.
8. **ADK Plugin** — `agent/argus_plugin/plugin.py` so Prem can test the full agent flow.
9. **Other CRUD endpoints** — Agent keys, payment methods.
10. **A2A endpoint** — Time-boxed to 3 hours. Agent Card + /a2a JSON-RPC handler.
11. **Docker + deploy** — Dockerfile, docker-compose.yml, Dockploy setup.
12. **README.md + ARCHITECTURE.md** — For Code Quality judging score.

## Database Tables (10 Total)

All defined in argus-data-spec.md Section 2:
- `users` — User accounts
- `profiles` — Agent profiles (formerly `agents`), each with own categories/rules/keys
- `payment_methods` — Funding sources with `method_type` + `detail` JSON
- `spending_categories` — Per-profile: Footwear, Electronics, Travel, General
- `category_rules` — Immutable rows (new row per change, for Hedera audit). Includes CUSTOM_RULE type for AI-evaluated free-text rules.
- `connection_keys` — API keys connecting agents to profiles (prefix: `argus_ck_`, with optional `expires_at`)
- `transactions` — Slim: request_data JSON + status + denormalized user_id
- `evaluations` — AI categorization + rules engine results + decision + risk_flags (one per transaction)
- `human_approvals` — Approval lifecycle with transaction_id + evaluation_id (only when HUMAN_NEEDED)
- `virtual_cards` — Issued single-use scoped cards for approved purchases

Use UUID strings as primary keys: `id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`

## API Endpoints I Build

All at `http://localhost:8000/api/v1`. Full request/response shapes in argus-data-spec.md Section 3.

**Auth (no auth required):**
- `POST /auth/register` → creates user + default category + default rules
- `POST /auth/login` → returns JWT token

**Agent endpoints (agent key auth):**
- `POST /evaluate` — THE critical endpoint. Receives purchase request, runs Gemini + rules engine, returns decision + optional virtual card.
- `GET /transactions/{id}/status` — Plugin polls this during human approval flow.

**Dashboard endpoints (JWT auth):**
- `GET /transactions` — List transactions (filterable, paginated)
- `GET /transactions/{id}` — Full transaction detail
- `POST /transactions/{id}/approve` — User approves pending transaction
- `POST /transactions/{id}/deny` — User denies pending transaction
- `GET /categories` — List categories with rules + spending totals
- `POST /categories` — Create new category
- `PUT /categories/{id}` — Edit category
- `GET /agent-keys` — List agent keys (prefix only)
- `POST /agent-keys` — Generate new key (returns full key ONCE)
- `DELETE /agent-keys/{id}` — Revoke key
- `GET /payment-methods` — List payment methods
- `POST /payment-methods` — Add payment method
- `WS /ws/dashboard` — Real-time transaction updates (JWT via query param)
- `GET /health` — Health check

**Auth logic:** Check `Authorization: Bearer <token>` header. If token starts with `argus_ck_`, look up in connection_keys table → resolve profile_id → user_id. Otherwise, decode as JWT.

## POST /evaluate Pipeline (The Most Important Thing I Build)

10-step pipeline — full details in argus-data-spec.md Section 3.4 and argus-teammate-guide.md Section 1.6:

1. Validate agent key → resolve user_id
2. Extract merchant domain from merchant_url
3. Create transaction row (status: PENDING_EVALUATION)
4. Load user's spending categories
5. Call Gemini 2.0 Flash for categorization + risk assessment
6. Match category from Gemini response
7. Load rules for matched category
8. Run deterministic rules engine (evaluate every rule, record results)
9. Make decision: APPROVE / DENY / HUMAN_NEEDED
10. Execute decision (issue card if approved, broadcast via WebSocket)

## Rules Engine Decision Priority

1. BLOCK_CATEGORY → DENY
2. Hard-fail (MAX_PER_TRANSACTION, DAILY/WEEKLY/MONTHLY_LIMIT, MERCHANT_BLACKLIST) → DENY
3. CUSTOM_RULE failed → HUMAN_NEEDED (AI-evaluated rules get human review)
4. ALWAYS_REQUIRE_APPROVAL → HUMAN_NEEDED
5. AUTO_APPROVE_UNDER failed (price above threshold) → HUMAN_NEEDED
6. Gemini intent_match < 0.5 or critical risk_flags → HUMAN_NEEDED
7. All rules pass → APPROVE

## Transaction Status Lifecycle

```
PENDING_EVALUATION
 ├── AI_APPROVED → COMPLETED / EXPIRED / FAILED
 ├── AI_DENIED
 └── HUMAN_NEEDED
      ├── HUMAN_APPROVED → COMPLETED / EXPIRED / FAILED
      ├── HUMAN_DENIED
      └── HUMAN_TIMEOUT
```

## Seed Data

Pre-populate on startup if demo user doesn't exist. Full data in argus-data-spec.md Section 10:
- **Demo user:** demo@argus.dev / argus2026
- **Payment methods:** Visa ending 4242 (default), Amex ending 1234
- **Categories:** Footwear, Electronics, Travel, General (default) — each with specific rules
- **Connection key:** `argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e`

## Integration Checkpoints with Prem

- **Hour ~2:** Auth working. Prem can POST /login and get a JWT.
- **Hour ~4:** GET /transactions returns data. WebSocket sends messages.
- **Hour ~6:** POST /evaluate fully working. Plugin built. First end-to-end test.
- **Hour ~8:** Approve/deny working. WebSocket broadcasts approvals.
- **Hour ~10:** Everything deployed.

## Environment Variables

```bash
ARGUS_DATABASE_URL=sqlite:///argus.db
ARGUS_JWT_SECRET=argus-hackathon-secret-change-in-prod
ARGUS_JWT_EXPIRY_HOURS=24
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_EVAL_MODEL=gemini-2.0-flash
USE_MOCK_CARDS=true
ARGUS_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Important Notes

- Use mock card issuer, NOT Lithic sandbox. Simpler and no external dependency.
- SQLite with `check_same_thread=False` for FastAPI async.
- CORS must allow Prem's frontend origin (localhost:5173 for Vite dev server).
- WebSocket auth: JWT token passed as query param `/ws/dashboard?token=eyJ...`
- Gemini evaluation prompt is in argus-data-spec.md Section 9.1 — copy it exactly.
- If Gemini fails, retry once then fall back to keyword-based categorization.
- A2A is time-boxed to 3 hours. If not working cleanly, skip — mention in pitch only.
