# ARGUS — Project Overview
## The Payment Guardian for AI Agents
### LIVE AI Ivy Plus Hackathon 2026

---

## What Is Argus?

Argus is an **AI agent payment authorization system** — a middleware layer that sits between any AI shopping agent and the financial transaction. When an AI agent tries to buy something on behalf of a user, Argus intercepts the purchase request, evaluates it against user-defined spending rules using AI-powered categorization, and either approves (issuing a scoped single-use virtual card), denies (with explanation), or escalates to the user for manual approval in real-time.

**The one-liner:** Argus is the Visa network for AI agents — every purchase goes through us, and we make sure it's the right one.

**The mythology:** Argus Panoptes was the all-seeing giant of Greek mythology, covered in a hundred eyes that never all closed at once. Our Argus watches every AI agent transaction with the same vigilance.

---

## Why This Matters

AI agents are rapidly moving from answering questions to taking actions — including spending money. The market for agentic commerce is projected to reach over $1 trillion. But there's a fundamental trust gap: how does a user know their AI agent will spend their money responsibly?

Today, if you give an AI agent your credit card, you're trusting it completely. There's no spending limits, no merchant restrictions, no category budgets, no human approval for big purchases. Argus solves this by creating a control layer between the agent and the money.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER'S MACHINE                                │
│                                                                       │
│  ┌──────────────────┐       ┌──────────────────────────────────────┐  │
│  │  Web Dashboard   │──────▶│          Argus Core API              │  │
│  │  (React + Vite)  │◀──────│          (FastAPI)                   │  │
│  │  Port 3000       │  HTTP │          Port 8000                   │  │
│  │                  │  + WS │                                      │  │
│  └──────────────────┘       │  ┌───────────┐  ┌────────────────┐  │  │
│                             │  │  Rules    │  │  Gemini 2.0    │  │  │
│  ┌──────────────────┐       │  │  Engine   │  │  Flash (eval)  │  │  │
│  │  ADK Agent       │       │  └───────────┘  └────────────────┘  │  │
│  │  (Gemini CU)     │       │  ┌───────────┐  ┌────────────────┐  │  │
│  │                  │       │  │  Mock     │  │  Database      │  │  │
│  │  ┌────────────┐  │       │  │  Card     │  │  (SQLite)      │  │  │
│  │  │ Argus ADK  │──┼──────▶│  │  Issuer   │  └────────────────┘  │  │
│  │  │ Plugin     │◀─┼───────│  └───────────┘                      │  │
│  │  └────────────┘  │  HTTP │  ┌───────────┐                      │  │
│  │                  │       │  │  WebSocket│                      │  │
│  │  ┌────────────┐  │       │  │  Manager  │                      │  │
│  │  │ Playwright │──┼──────▶│  └───────────┘                      │  │
│  │  │ Browser    │  │       │                                      │  │
│  │  └────────────┘  │       │  ┌───────────────────────────────┐  │  │
│  └──────────────────┘       │  │  A2A Endpoint (/.well-known/  │  │  │
│                             │  │  agent.json + /a2a handler)   │  │  │
│                             │  └───────────────────────────────┘  │  │
│                             └──────────────────────────────────────┘  │
│                                                                       │
│         ┌─────────────────────────────────────────────────┐           │
│         │  Real E-commerce Sites (Amazon, Target, etc.)   │           │
│         └─────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Core Flow (What Happens When the Agent Shops)

This is the most important thing to understand. Everything we build serves this flow:

```
1. USER tells agent: "Buy me running shoes under $80"

2. AGENT (Gemini Computer Use) opens a browser, navigates to Amazon,
   browses products, compares prices and reviews, picks one,
   adds to cart, navigates to checkout.

3. AGENT reaches the payment form. Instead of typing a credit card,
   it calls request_purchase(product_name, price, merchant_url, ...).

4. ARGUS PLUGIN (living inside the agent's process) intercepts this call
   via before_tool_callback. It POSTs the purchase details to the
   Argus Core API.

5. ARGUS CORE API:
   a. Validates the agent's connection key → resolves to profile → to user
   b. Sends product details to Gemini 2.0 Flash → gets category
      (e.g., "Footwear") + risk assessment + intent match score
   c. Loads user's rules for that category (budget limits,
      merchant whitelist, auto-approve threshold, etc.)
   d. Runs deterministic rules engine against each rule
   e. Makes decision: APPROVE, DENY, or HUMAN_NEEDED

6. IF APPROVED: Argus generates a scoped single-use virtual card
   (mock for hackathon) with:
   - Spending limit = price + 15% buffer (for tax/shipping)
   - Merchant lock = only works at that merchant domain
   - Expires in 30 minutes
   The card details are returned to the plugin → to the agent.

7. IF DENIED: Reason returned to agent. Agent tells user and
   searches for alternatives (cheaper option, different merchant).

8. IF HUMAN_NEEDED: Dashboard gets real-time WebSocket notification.
   User sees approve/deny dialog with product details, price, and
   Argus's reasoning. User clicks approve → card issued → returned
   to agent. Plugin polls for the decision.

9. AGENT receives card details and fills them into the checkout form
   using Playwright keyboard actions.

10. DASHBOARD shows the entire flow in real-time — transaction appears
    as "Evaluating...", then updates to "Approved" or "Denied" with
    full details (category, rules checked, Gemini reasoning).
```

---

## The Five Components We Are Building

### 1. Argus Core API (FastAPI — Python)
**Owner: Teammate**

The brain of the system. A REST API with:
- Auth endpoints (JWT for dashboard, connection key for agent)
- The `/evaluate` endpoint (the critical one — receives purchase request, runs Gemini + rules engine, returns decision + optional virtual card)
- Transaction management (list, detail, approve, deny)
- Category & rules management (CRUD)
- WebSocket for real-time dashboard updates
- A2A endpoint for agent discoverability

### 2. Argus ADK Plugin (Python)
**Owner: Teammate**

A plugin that runs inside the ADK agent process. It:
- Intercepts `request_purchase` tool calls via `before_tool_callback`
- Sends purchase details to Core API
- Handles the three response types (approve → return card, deny → return reason, human_needed → poll until resolved)
- Also intercepts `type`/`input_text` calls to block any card number the agent tries to enter that wasn't issued by Argus (safety net)

### 3. ADK Shopping Agent (Python + Google ADK)
**Owner: Prem**

An AI agent using Gemini 2.5 Computer Use that:
- Takes natural language shopping requests from users
- Opens a Playwright browser and navigates real e-commerce sites
- Searches for products, compares options, picks the best match
- Calls `request_purchase` before entering payment info (enforced by system prompt + plugin)
- If denied, searches for alternatives automatically
- If approved, fills checkout form with Argus-issued virtual card

### 4. Web Dashboard (React + Vite + TailwindCSS + shadcn/ui)
**Owner: Prem**

A professional fintech dashboard that:
- Shows real-time transaction feed via WebSocket
- Lets users approve/deny purchases waiting for human review
- Displays spending categories and rules configuration
- Shows transaction details with Gemini's reasoning and rule checks
- Supports login/auth with JWT

### 5. A2A Endpoint (Part of Core API)
**Owner: Teammate**

A Google A2A protocol implementation that:
- Serves an Agent Card at `/.well-known/agent.json` describing Argus's capabilities
- Exposes a `/a2a` JSON-RPC endpoint that any A2A-compatible agent can call
- Translates A2A task requests into our existing `/evaluate` flow
- Exists primarily as a tech innovation differentiator for the pitch

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend API | FastAPI (Python 3.11+) | Fast, async, great for APIs, easy WebSocket |
| Database | SQLite + SQLAlchemy | Zero infrastructure, persistent Docker volume |
| Frontend | React + Vite + TailwindCSS | Standard, fast build, modern |
| UI Components | shadcn/ui (Radix + Tailwind) | Professional fintech look with minimal effort |
| Agent Framework | Google ADK (Python) | Google-sponsored hackathon, native Gemini integration |
| Agent Browser | Playwright (via ADK ComputerUseToolset) | Standard browser automation, works with ADK |
| Agent Model | Gemini 2.5 Computer Use | Visual browsing + action taking |
| Evaluation LLM | Gemini 2.0 Flash | Fast categorization + risk assessment |
| Virtual Cards | Mock issuer | Realistic card numbers, no sandbox timing risk |
| Auth (Dashboard) | JWT (python-jose + bcrypt) | Standard, simple |
| Auth (Agent) | Connection key (`argus_ck_` prefix) | Resolves key → profile → user |
| Real-time | FastAPI native WebSocket | No extra dependency |
| Deploy Frontend | Vercel | Free, instant, git-push deploy |
| Deploy Backend | Dockploy (Docker + persistent SQLite) | Self-hosted, persistent data |

---

## Branding

- **Name:** ARGUS
- **Tagline:** "The Payment Guardian for AI Agents"
- **Theme:** Light mode with dark sidebar
- **Color Palette:**
  - Background: White (#FFFFFF) / Light gray (#F8FAFC)
  - Sidebar/Header: Dark slate (#1E293B)
  - Primary accent: Teal (#0D9488 / #14B8A6)
  - Text: Dark slate (#0F172A)
  - Approve/Success: Green (#22C55E)
  - Deny/Error: Red (#EF4444)
  - Pending/Warning: Amber (#F59E0B)
  - Card backgrounds: White with subtle border (#E2E8F0)
- **Font:** Inter
- **Logo:** Shield + eye icon (SVG) — Argus = the all-seeing guardian
- **Design Philosophy:** Clean, professional fintech. Think Stripe dashboard meets Linear.

---

## Demo Scenario (What We Show in the Video)

**One deep, end-to-end scenario (Option A):**

1. Open dashboard — show configured spending categories and rules (Footwear: max $200/transaction, auto-approve under $80, daily limit $300, whitelisted merchants only)
2. Open agent chat — type: "Find me running shoes under $80"
3. Agent opens Amazon in Playwright browser, searches, browses results
4. Agent finds shoes at ~$95 → calls request_purchase
5. Dashboard shows transaction appear in real-time: "EVALUATING..."
6. Argus evaluates: $95 > $80 auto-approve threshold → **DENIED**
7. Dashboard shows red DENIED badge with reason
8. Agent automatically searches for cheaper alternatives
9. Agent finds different shoes at ~$60 → calls request_purchase again
10. Argus evaluates: $60 < $80, amazon.com is whitelisted → **APPROVED**
11. Dashboard shows green APPROVED badge, virtual card issued
12. Agent fills checkout form with Argus virtual card details
13. Dashboard shows transaction complete

**Why this works:** It shows the DENY → retry → APPROVE loop in one flow, proving the system actually controls agent behavior. The real-time dashboard updates are the visual climax.

---

## Project Structure

```
argus/
├── backend/                    # [TEAMMATE'S DOMAIN]
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app, CORS, startup
│   │   ├── config.py           # Pydantic Settings from env
│   │   ├── database.py         # SQLAlchemy engine, session, Base
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
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
│
├── agent/                      # [SPLIT OWNERSHIP]
│   ├── argus_plugin/           # [TEAMMATE'S DOMAIN]
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── request_purchase.py
│   │   └── session_store.py
│   ├── shopping_agent/         # [PREM'S DOMAIN]
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── config.py
│   │   └── prompts.py
│   └── run_agent.py            # [PREM'S DOMAIN]
│
├── frontend/                   # [PREM'S DOMAIN]
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── layout/         # Sidebar, Header, Layout
│   │   │   ├── transactions/   # TransactionFeed, TransactionCard, StatusBadge
│   │   │   ├── categories/     # CategoryList, CategoryCard, RuleTag
│   │   │   ├── approvals/      # ApprovalQueue, ApprovalDialog
│   │   │   └── auth/           # LoginForm
│   │   ├── pages/              # LoginPage, DashboardPage, CategoriesPage, etc.
│   │   ├── hooks/              # useWebSocket, useAuth, useTransactions
│   │   ├── lib/                # api.ts, types.ts, utils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── docker-compose.yml
├── .env
├── README.md
└── ARCHITECTURE.md
```

---

## Ownership Boundaries

**RULE: Do not edit files in the other person's domain without coordinating first.**

| Domain | Owner | Files |
|--------|-------|-------|
| Backend API | Teammate | `backend/` entire directory |
| ADK Plugin | Teammate | `agent/argus_plugin/` |
| A2A Endpoint | Teammate | `backend/a2a/` |
| Docker/Deploy | Teammate | `Dockerfile`, `docker-compose.yml` |
| Shopping Agent | Prem | `agent/shopping_agent/`, `agent/run_agent.py` |
| Frontend | Prem | `frontend/` entire directory |
| Pitch/Video | Prem | `pitch/` directory |
| Shared | Coordinate | `.env`, `README.md`, `ARCHITECTURE.md` |

---

## Environment Variables

```bash
# === Argus Core API ===
ARGUS_DATABASE_URL=sqlite:///argus.db
ARGUS_JWT_SECRET=your-jwt-secret-change-in-production
ARGUS_JWT_EXPIRY_HOURS=24

# === Gemini ===
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_EVAL_MODEL=gemini-2.0-flash
GEMINI_CU_MODEL=gemini-2.5-computer-use-preview-10-2025

# === Virtual Cards ===
USE_MOCK_CARDS=true

# === Hedera (SKIP for build, pitch only) ===
USE_HEDERA=false

# === Agent Configuration ===
ARGUS_API_URL=http://localhost:8000/api/v1
ARGUS_CONNECTION_KEY=argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e

# === Dashboard ===
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws/dashboard
```

---

## Ports

| Service | Port | URL |
|---------|------|-----|
| Argus Core API | 8000 | http://localhost:8000 |
| React Dashboard | 3000 | http://localhost:3000 |
| ADK Dev UI | 8080 | http://localhost:8080 |

---

## Seed Data (Pre-loaded for Demo)

**Demo User:** demo@argus.dev / argus2026

**Payment Methods:**
- Visa ending 4242 (default)
- Amex ending 1234

**Spending Categories + Rules:**

| Category | Auto-Approve Under | Max Per Transaction | Daily Limit | Monthly Limit | Merchant Whitelist | Require Approval |
|----------|-------------------|--------------------|-----------|--------------|--------------------|-----------------|
| Footwear | $80 | $200 | $300 | — | amazon.com, nike.com, zappos.com, target.com, bestbuy.com | No |
| Electronics | $100 | $500 | — | $2,000 | — | No |
| Travel | — | $2,000 | — | $5,000 | — | **YES (always)** |
| General (default) | $50 | $500 | $1,000 | — | — | No |

**Connection Key:** `argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e`

---

## Build Priority (If Time Runs Out)

Build in this order. Items 1-3 are non-negotiable:

1. **Core API** — evaluate endpoint, rules engine, mock cards — without this, nothing works
2. **Dashboard basics** — login, transaction feed, status badges — what judges SEE
3. **Agent working** — basic shopping + request_purchase — the wow factor
4. **Dashboard polish** — approval queue, categories page, transaction detail — Design score
5. **A2A endpoint** — tech innovation differentiator
6. **Deployment** — Docker + Vercel
7. **Video production** — MUST happen, minimum 2 hours budgeted
8. **README + ARCHITECTURE.md** — Code Quality score

**Cut list (first to drop if behind):**
1. A2A → mention in pitch only
2. Analytics charts → skip entirely
3. Deployment → demo from localhost
4. Transaction detail page → show info inline in feed

**NEVER cut:** Core evaluate endpoint, transaction feed, working agent (even if pre-recorded), pitch video.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Gemini Computer Use is flaky/slow | Pre-record successful agent run. Have backup video. |
| Amazon blocks Playwright | Try Target, Best Buy, or Google Shopping instead. |
| WebSocket disconnects during demo | Fallback: manual refresh. Test stability before recording. |
| A2A implementation takes too long | Time-box to 3 hours. If not working, pitch-only. |
| Gemini rate limiting | Cache demo evaluation results. Pre-seed successful transaction. |
| Build takes longer than expected | Follow priority order above. |

---

## Reference Documents

- **argus-data-spec.md** — Complete database schema, all API contracts, all module interfaces, Gemini prompts, seed data. THE source of truth for all integration points.
- **argus-teammate-guide.md** — Everything the backend person needs.
- **argus-prem-guide.md** — Everything Prem needs (frontend + agent + pitch).
- **argus-team-split.md** — Hour-by-hour build sequence.

---

## Hackathon Context

- **Event:** LIVE AI Ivy Plus Hackathon 2026 (online — originally onsite, cancelled)
- **Judging:** 8 criteria, 1-10 each: UI, UX, Tech Innovation, Code Quality, Production Values, Pitch, Market Fit, Disruptive Potential
- **Deliverables:** 2-3 minute pitch video, Devpost submission, GitHub repo
- **Global judges** evaluate videos over 2 weeks. They do NOT clone repos or test locally.
- **What wins:** Working demo > code quality. Professional UI > feature count. Compelling story > technical depth. Real API integrations > mocks.
