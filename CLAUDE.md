# CLAUDE.md — Argus Project Context

## What Is This Project?

Argus is an AI agent payment authorization system being built for the LIVE AI Ivy Plus Hackathon 2026. It intercepts AI shopping agent purchases, evaluates them against user-defined spending rules using Gemini AI, and issues scoped virtual cards for approved transactions.

## Who Am I (The Developer Using This CLI)?

I am **Prem** — I own the frontend, shopping agent, pitch, and project management. See `argus-prem-guide.md` for my full build guide.

## My Scope — What I Build

1. **Web Dashboard** — React + Vite + TailwindCSS + shadcn/ui (in `frontend/`)
2. **ADK Shopping Agent** — Google ADK + Gemini Computer Use (in `agent/shopping_agent/` and `agent/run_agent.py`)
3. **Pitch & Video** — Script, slides, screen recording (in `pitch/`)

## What I Do NOT Touch

- `backend/` — My teammate builds this (FastAPI, database, all API endpoints)
- `agent/argus_plugin/` — My teammate builds the ADK plugin
- `docker-compose.yml`, `Dockerfile` — My teammate handles deployment

## Key Reference Documents (READ THESE)

- **`argus-data-spec.md`** — THE source of truth for all API contracts, database schemas, TypeScript types, WebSocket messages, Gemini prompts, and seed data. Reference this for every integration point.
- **`argus-prem-guide.md`** — My detailed build guide with hour-by-hour plan, component structure, page-by-page instructions, and code snippets.
- **`argus-project-overview.md`** — High-level architecture, core flow, tech stack, branding, demo scenarios.
- **`argus-teammate-guide.md`** — What my teammate is building. Useful for understanding what APIs I'll consume.

## Tech Stack (My Parts)

- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui (New York style, Slate base, CSS variables)
- **Routing:** react-router-dom
- **HTTP Client:** axios
- **Icons:** lucide-react
- **Font:** Inter
- **Agent Framework:** Google ADK (Python)
- **Agent Model:** Gemini 2.5 Computer Use (`gemini-2.5-computer-use-preview-10-2025`)
- **Agent Browser:** Playwright (via ADK ComputerUseToolset)

## Branding & Design

- **Theme:** Light mode with dark sidebar
- **Primary accent:** Teal (#0D9488 / #14B8A6)
- **Sidebar:** Dark slate (#1E293B)
- **Background:** White (#FFFFFF) / Light gray (#F8FAFC)
- **Approve:** Green (#22C55E)
- **Deny:** Red (#EF4444)
- **Pending:** Amber (#F59E0B)
- **Font:** Inter
- **Design philosophy:** Clean, minimal, professional fintech. Stripe Dashboard meets Linear. All components use shadcn/ui.

## Project Structure

```
argus/
├── frontend/                   # [MY DOMAIN]
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui (auto-generated)
│   │   │   ├── layout/         # AppLayout, AppSidebar (with ProfileSwitcher), Header
│   │   │   ├── profiles/       # ProfileSwitcher
│   │   │   ├── transactions/   # TransactionFeed, TransactionCard, StatusBadge
│   │   │   ├── categories/     # CategoryList, CategoryCard, RuleTag
│   │   │   ├── approvals/      # ApprovalQueue, ApprovalDialog
│   │   │   └── auth/           # LoginForm
│   │   ├── pages/              # LoginPage, DashboardPage, CategoriesPage, ApprovalsPage, ConnectionKeysPage, PaymentMethodsPage, TransactionDetailPage
│   │   ├── hooks/              # useAuth, useProfile, useWebSocket, useTransactions
│   │   ├── lib/                # api.ts, types.ts, utils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── agent/
│   ├── shopping_agent/         # [MY DOMAIN]
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── config.py
│   │   └── prompts.py
│   └── run_agent.py            # [MY DOMAIN]
├── pitch/                      # [MY DOMAIN]
├── argus-data-spec.md          # Source of truth for all contracts
├── argus-prem-guide.md         # My build guide
├── argus-project-overview.md   # High-level overview
├── argus-teammate-guide.md     # Teammate's guide (for reference)
└── CLAUDE.md                   # This file
```

## Build Order (Follow This Sequence)

### Hours 0-2: Foundation
- Create Vite + React + Tailwind project in `frontend/`
- Install shadcn/ui components
- Set up React Router (login → protected routes)
- Build AppLayout (sidebar + header + content slot)
- Build AppSidebar with nav links
- Create `lib/types.ts` with all TypeScript interfaces (copy from argus-data-spec.md Sections 3.4-3.16)
- Create `lib/api.ts` with axios instance
- Build LoginPage + LoginForm

### Hours 2-4: Dashboard Core
- Build useAuth hook
- Build StatusBadge, TransactionCard, TransactionFeed
- Build DashboardPage with WebSocket integration
- Build useWebSocket hook

### Hours 4-6: Agent + More Pages
- Set up ADK shopping agent
- Build CategoriesPage, CategoryCard, RuleTag

### Hours 6-8: Approvals + Integration
- Build ApprovalQueue, ApprovalDialog, ApprovalsPage
- Build TransactionDetailPage
- Full end-to-end testing with teammate's backend

### Hours 8-10: Polish + Agent Reliability
- Loading skeletons, empty states, animations
- Agent reliability testing

### Hours 10-12: Demo + Video
- Demo rehearsal, screen recording, video editing, Devpost submission

## API Endpoints I Consume

All endpoints are at `http://localhost:8000/api/v1` (backend runs on port 8000).

**Auth:**
- `POST /auth/login` → `{email, password}` → `{user, token}`

**Profiles:**
- `GET /profiles` → list user's profiles
- `POST /profiles` → create new profile

**Transactions:**
- `GET /transactions?limit=20&sort=created_at_desc` → transaction list (with joined evaluation data)
- `POST /transactions/{id}/approve` → approve HUMAN_NEEDED transaction
- `POST /transactions/{id}/deny` → deny HUMAN_NEEDED transaction

**Categories (profile-scoped):**
- `GET /categories?profile_id=X` → categories with rules + spending totals for selected profile

**Connection Keys (profile-scoped):**
- `GET /connection-keys?profile_id=X` → list keys for selected profile
- `POST /connection-keys` → generate new key (returns full key ONCE)
- `DELETE /connection-keys/{id}` → revoke key

**Payment Methods (account-level):**
- `GET /payment-methods` → list all funding sources
- `POST /payment-methods` → add new method (with method_type + detail JSON)

**WebSocket:**
- `ws://localhost:8000/ws/dashboard?token=JWT` → real-time updates

Message types: `TRANSACTION_CREATED`, `TRANSACTION_DECIDED`, `APPROVAL_REQUIRED`, `VIRTUAL_CARD_USED`

**Transaction status values:** `PENDING_EVALUATION`, `AI_APPROVED`, `AI_DENIED`, `HUMAN_NEEDED`, `HUMAN_APPROVED`, `HUMAN_DENIED`, `HUMAN_TIMEOUT`, `COMPLETED`, `EXPIRED`, `FAILED`

## Important Notes

- If backend isn't ready yet, mock data locally and build UI against the TypeScript types. Swap in real API calls later.
- The DashboardPage (transaction feed) is the most important page — spend the most time here.
- Use shadcn/ui for ALL components. No custom UI primitives.
- Demo credentials: demo@argus.dev / argus2026
- Frontend runs on port 5173 (Vite default) or 3000.
- **Sidebar has a ProfileSwitcher** — categories, rules, and connection keys are all scoped to the selected profile. Payment methods are account-level (not profile-scoped).
- **Status badges:** Green for `AI_APPROVED`/`HUMAN_APPROVED`, Red for `AI_DENIED`/`HUMAN_DENIED`, Amber for `HUMAN_NEEDED`, Blue for `PENDING_EVALUATION`, Gray for `HUMAN_TIMEOUT`/`EXPIRED`.
- **The data spec (argus-data-spec.md) is the v2.0 source of truth.** Key changes from v1: profiles (not agents), connection_keys (not agent_keys, prefix `argus_ck_`), split transactions into transactions + evaluations + human_approvals tables, new status lifecycle, CUSTOM_RULE type, no spending_ledger.
