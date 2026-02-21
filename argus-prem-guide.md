# ARGUS — Prem's Build Guide
## Frontend + Agent + Pitch + PM
### Owner: Prem

---

## Your Scope

You are building three things + managing the project:

1. **Web Dashboard** (React + Vite + shadcn/ui) — The professional fintech UI that judges see
2. **ADK Shopping Agent** (Google ADK + Gemini Computer Use) — The AI that shops on real sites
3. **Pitch & Video** — Script, slides, screen recording, market research
4. **Project Management** — Integration coordination, timeline, demo rehearsal

**You do NOT touch:** `backend/`, `agent/argus_plugin/`, `docker-compose.yml`, `Dockerfile`

---

## PART 1: WEB DASHBOARD

### 1.1 Project Setup

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npx shadcn@latest init    # Choose: New York style, Slate base color, CSS variables YES
```

**Install shadcn components you'll need:**
```bash
npx shadcn@latest add button card badge dialog input label table
npx shadcn@latest add sidebar sheet separator scroll-area
npx shadcn@latest add alert toast tabs avatar dropdown-menu
npx shadcn@latest add skeleton tooltip popover select textarea
```

**Additional dependencies:**
```bash
npm install react-router-dom axios lucide-react
npm install -D @types/react-router-dom
```

---

### 1.2 Branding & Theme Config

**tailwind.config.ts — extend with Argus colors:**
```typescript
// Light mode with dark sidebar
// Primary: Teal (#0D9488 / #14B8A6)
// Sidebar: Dark slate (#1E293B)
// Background: White (#FFFFFF) / Light gray (#F8FAFC)
// Cards: White with border (#E2E8F0)
// Text: Dark slate (#0F172A)
// Approve: Green (#22C55E)
// Deny: Red (#EF4444)
// Pending: Amber (#F59E0B)
```

**Font:** Inter — import via Google Fonts or install `@fontsource/inter`

**Design philosophy:** Clean, minimal, professional fintech. Dark sidebar (slate) + white content area. Think Stripe Dashboard meets Linear. Every component uses shadcn/ui for consistency.

---

### 1.3 Application Structure

```
frontend/src/
├── components/
│   ├── ui/                       # shadcn/ui (auto-generated)
│   ├── layout/
│   │   ├── AppLayout.tsx         # Main layout: sidebar + header + content area
│   │   ├── AppSidebar.tsx        # Dark slate sidebar with nav links
│   │   └── Header.tsx            # Top bar with user info
│   ├── transactions/
│   │   ├── TransactionFeed.tsx   # Real-time scrollable list of transactions
│   │   ├── TransactionCard.tsx   # Single transaction row/card in the feed
│   │   ├── TransactionDetail.tsx # Expanded view: rules, Gemini reasoning, card info
│   │   └── StatusBadge.tsx       # Colored badges: APPROVED (green), DENIED (red), PENDING (amber)
│   ├── categories/
│   │   ├── CategoryList.tsx      # Grid/list of spending categories
│   │   ├── CategoryCard.tsx      # Single category with rules listed
│   │   └── RuleTag.tsx           # Pill/badge showing rule type + value
│   ├── approvals/
│   │   ├── ApprovalQueue.tsx     # List of pending transactions needing approval
│   │   └── ApprovalDialog.tsx    # Modal: product details + approve/deny buttons
│   └── auth/
│       └── LoginForm.tsx         # Email + password + submit
├── pages/
│   ├── LoginPage.tsx             # Full-screen login centered
│   ├── DashboardPage.tsx         # Main page: transaction feed + approval alerts
│   ├── TransactionDetailPage.tsx # Full detail view for one transaction
│   ├── CategoriesPage.tsx        # All categories + their rules
│   └── ApprovalsPage.tsx         # Dedicated approval queue view
├── hooks/
│   ├── useAuth.ts                # JWT token management, login/logout
│   ├── useWebSocket.ts           # WebSocket connection, auto-reconnect
│   └── useTransactions.ts        # Fetch + real-time update of transactions
├── lib/
│   ├── api.ts                    # Axios instance with auth interceptor
│   ├── types.ts                  # TypeScript interfaces matching API responses
│   └── utils.ts                  # Formatters: currency, dates, status colors
├── App.tsx                       # Router: public (login) + protected (dashboard)
└── main.tsx                      # Entry point
```

---

### 1.4 TypeScript Types (lib/types.ts)

These match the API response shapes exactly. Copy from **argus-data-spec.md** Sections 3.4-3.16.

```typescript
// === Auth ===
interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

// === Agents ===
interface Agent {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthResponse {
  user: User;
  token: string;
}

// === Transactions ===
type TransactionStatus = 
  | "PENDING_EVALUATION" 
  | "AI_APPROVED" 
  | "AI_DENIED" 
  | "HUMAN_NEEDED" 
  | "HUMAN_APPROVED" 
  | "HUMAN_DENIED" 
  | "HUMAN_TIMEOUT"
  | "COMPLETED" 
  | "EXPIRED" 
  | "FAILED";

type Decision = "APPROVE" | "DENY" | "HUMAN_NEEDED";

interface RuleCheck {
  rule_id: string;
  rule_type: string;
  threshold?: number;
  actual_value?: number;
  breakdown?: { previously_spent: number; this_transaction: number };
  prompt?: string;          // For CUSTOM_RULE type
  passed: boolean;
  detail: string;
  merchant_domain?: string;
  whitelist?: string[];
}

interface AIEvaluation {
  category_name: string;
  category_confidence: number;
  intent_match: number;
  intent_summary: string;
  risk_flags: string[];     // Free-text array from AI
  reasoning: string;
}

interface VirtualCard {
  card_number: string;
  expiry_month: string;
  expiry_year: string;
  cvv: string;
  last_four: string;
  spend_limit: number;
  merchant_lock: string;
  expires_at: string;
}

// Transaction request_data (stored as JSON on transaction)
interface RequestData {
  product_name: string;
  product_url?: string;
  price: number;
  currency: string;
  merchant_name: string;
  merchant_domain: string;
  merchant_url: string;
  conversation_context?: string;
  metadata?: Record<string, any>;
}

// Evaluation data (joined from evaluations table)
interface EvaluationSummary {
  decision: Decision;
  category_name?: string;
  category_confidence?: number;
  intent_match?: number;
  decision_reasoning?: string;
  risk_flags?: string[];
  rules_checked?: RuleCheck[];
}

interface Transaction {
  id: string;
  status: TransactionStatus;
  request_data: RequestData;
  evaluation?: EvaluationSummary;  // Joined from evaluations table
  virtual_card_last_four?: string;
  virtual_card_status?: string;
  created_at: string;
  updated_at: string;
}

interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

// === Categories ===
interface CategoryRule {
  id: string;
  rule_type: string;
  value: string;
  is_active: boolean;
}

interface PaymentMethod {
  id: string;
  nickname: string;
  method_type: "CREDIT_CARD" | "DEBIT_CARD" | "BANK_ACCOUNT" | "CRYPTO_WALLET";
  status: string;
  is_default: boolean;
  detail: Record<string, any>;  // Type-specific data (brand, last4, etc.)
}

interface SpendingCategory {
  id: string;
  name: string;
  description?: string;
  keywords: string[];
  is_default: boolean;
  payment_method?: { id: string; nickname: string; method_type: string };
  rules: CategoryRule[];
  spending_today: number;
  spending_this_week: number;
  spending_this_month: number;
}

// === Profiles ===
interface Profile {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

// === Connection Keys ===
interface ConnectionKey {
  id: string;
  key_prefix: string;
  label: string;
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  created_at: string;
}

// === WebSocket Messages ===
type WSMessageType = 
  | "TRANSACTION_CREATED" 
  | "TRANSACTION_DECIDED" 
  | "APPROVAL_REQUIRED" 
  | "VIRTUAL_CARD_USED";

interface WSMessage {
  type: WSMessageType;
  data: Record<string, any>;
}

// === Agent Keys ===
interface AgentKey {
  id: string;
  key_prefix: string;
  label: string;
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
}
```

---

### 1.5 API Client (lib/api.ts)

```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Add JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('argus_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 → redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('argus_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

### 1.6 WebSocket Hook (hooks/useWebSocket.ts)

```typescript
import { useEffect, useRef, useCallback, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/dashboard';

export function useWebSocket(onMessage: (msg: WSMessage) => void) {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  
  const connect = useCallback(() => {
    const token = localStorage.getItem('argus_token');
    if (!token) return;
    
    ws.current = new WebSocket(`${WS_URL}?token=${token}`);
    
    ws.current.onopen = () => setConnected(true);
    
    ws.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      onMessage(msg);
    };
    
    ws.current.onclose = () => {
      setConnected(false);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
    
    ws.current.onerror = () => ws.current?.close();
  }, [onMessage]);
  
  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);
  
  return { connected };
}
```

---

### 1.7 Page-by-Page Build Guide

#### Page 1: LoginPage

**What it shows:** Centered card with Argus logo, email input, password input, login button. Clean, branded.

**API calls:**
- `POST /api/v1/auth/login` with `{email, password}`
- Store `token` in localStorage
- Redirect to `/` (dashboard)

**Design notes:**
- Full-screen, light background, centered card
- Argus logo/name at top of card
- "The Payment Guardian for AI Agents" tagline below logo
- Simple form: email, password, "Sign In" button
- Error display if invalid credentials

---

#### Page 2: DashboardPage (THE money shot)

**What it shows:** Real-time transaction feed. This is what judges see in the demo video.

**API calls:**
- `GET /api/v1/transactions?limit=20&sort=created_at_desc` on mount
- WebSocket for live updates

**Layout:**
- Full-width content area (sidebar is part of AppLayout)
- Header: "Transactions" title + maybe total count
- Transaction feed: scrollable list of TransactionCard components
- Each card shows: product name, price, merchant, category badge, status badge, time
- Status badges: Green "AI_APPROVED"/"HUMAN_APPROVED", Red "AI_DENIED"/"HUMAN_DENIED", Amber "HUMAN_NEEDED", Blue "EVALUATING...", Gray "HUMAN_TIMEOUT"
- When APPROVAL_REQUIRED arrives via WebSocket: show a prominent notification bar/toast at the top or inline with approve/deny buttons

**WebSocket handling:**
```typescript
function handleWSMessage(msg: WSMessage) {
  switch (msg.type) {
    case 'TRANSACTION_CREATED':
      // Add new transaction to top of feed with "EVALUATING..." status
      // Maybe a subtle animation: slide in from top
      break;
    case 'TRANSACTION_DECIDED':
      // Find transaction in feed, update status + add decision details
      // Green flash for approve, red flash for deny
      break;
    case 'APPROVAL_REQUIRED':
      // Show prominent approval notification
      // Could be inline card in feed with Approve/Deny buttons
      // Or a toast/dialog that draws attention
      break;
    case 'VIRTUAL_CARD_USED':
      // Update card status in detail view
      break;
  }
}
```

**This is the most important page.** Spend the most time here making it look polished.

---

#### Page 3: TransactionDetailPage

**What it shows:** Expanded view when you click a transaction. Shows everything: Gemini's AI reasoning, which rules passed/failed, virtual card info, timeline.

**Route:** `/transactions/:id`

**API calls:** Use transaction data already loaded, or `GET /api/v1/transactions/{id}` for full detail

**Layout sections:**
1. **Header:** Product name, price, merchant, status badge (large)
2. **AI Evaluation card:** Category detected (with confidence), intent match score, intent summary, risk flags (if any), Gemini's reasoning text
3. **Rules Evaluation card:** List of every rule checked — show each as a row with rule_type, threshold vs actual, pass/fail icon, detail string. Color-code: green checkmark for pass, red X for fail
4. **Virtual Card card (if approved):** Card number (masked: •••• •••• •••• 8847), spend limit, merchant lock, expires at, status
5. **Timeline:** Created → Evaluated → Decision → Card Issued → Card Used (each with timestamp)

---

#### Page 4: CategoriesPage

**What it shows:** All spending categories with their rules. The "control panel" that shows users how they've configured their spending guardrails.

**API calls:** `GET /api/v1/categories`

**Layout:**
- Grid of category cards (2 columns on desktop, 1 on mobile)
- Each card shows:
  - Category name (e.g., "Footwear") + description
  - Keywords as small pills/tags
  - Linked payment method (e.g., "Visa ending 4242")
  - Rules listed with clear formatting:
    - "Max per transaction: $200.00"
    - "Auto-approve under: $80.00"
    - "Daily limit: $300.00"
    - "Whitelisted merchants: amazon.com, nike.com, zappos.com"
  - Spending totals: Today: $45 / Week: $120 / Month: $350
  - Maybe a progress bar showing spend vs limit

**Nice-to-have:** Edit category button → opens form to change rules. But for demo, read-only display is fine — shows the system has configuration.

---

#### Page 5: ApprovalsPage

**What it shows:** Pending transactions that need human approval. Approve/deny buttons. This is for the human-in-the-loop demo scenario.

**API calls:**
- `GET /api/v1/transactions?status=HUMAN_NEEDED` on mount
- WebSocket for new approval requests
- `POST /api/v1/transactions/{id}/approve` or `/deny`

**Layout:**
- List of pending approval cards, each showing:
  - Product name, price, merchant
  - Category detected + confidence
  - Why it needs approval (e.g., "Travel purchases require your approval")
  - Countdown timer (timeout in X:XX)
  - Two buttons: green "Approve" + red "Deny"
  - Optional note field
- Empty state: "No pending approvals" with checkmark icon

**When user clicks Approve:**
1. Call `POST /transactions/{id}/approve` with optional note
2. Card updates to show "HUMAN_APPROVED" status
3. Transaction appears in main feed as approved

**When user clicks Deny:**
1. Call `POST /transactions/{id}/deny` with optional note
2. Card updates to show "HUMAN_DENIED" status
3. Agent receives denial and searches for alternatives

---

### 1.8 Layout Components

**AppSidebar.tsx:**
```
┌──────────────────────┐
│  🛡️ ARGUS            │  ← Logo + name
│  Payment Guardian     │  ← Tagline (small)
│                       │
│  ▼ Personal Shopper   │  ← ProfileSwitcher dropdown
│                       │
│  📊 Dashboard         │  ← Active: teal highlight
│  📂 Categories        │
│  ✅ Approvals    (2)  │  ← Badge with pending count
│  📄 Transactions      │  ← Full history
│  🔑 Connection Keys   │
│                       │
│  ─────────────────    │
│  💳 Payment Methods   │  ← Account-level (not profile-scoped)
│  demo@argus.dev       │  ← User info at bottom
│  Sign Out             │
└──────────────────────┘
```

- Dark slate (#1E293B) background
- White text, teal accent for active item
- Use shadcn/ui Sidebar component
- ProfileSwitcher switches the active profile — categories, rules, connection keys, and approvals are scoped to the selected profile
- Payment Methods is account-level (not scoped to profile)
- Pending approval count badge updates via WebSocket

---

### 1.9 Key UI Polish Items (What Makes It Look Professional)

These are the details that separate a hackathon project from a polished product:

1. **Loading skeletons** — Use shadcn Skeleton component while data loads. No blank screens.
2. **Empty states** — "No transactions yet. Your AI agent hasn't made any purchases." with an illustration or icon.
3. **Subtle animations** — New transactions slide in from top. Status badge changes have a brief color flash.
4. **Consistent spacing** — Use Tailwind's spacing scale consistently (p-4, gap-4, etc.)
5. **Hover states** — Transaction cards have subtle hover effect, clickable to detail view.
6. **Timestamps** — Show relative time ("2 min ago") with tooltip showing absolute time.
7. **Status colors everywhere** — Green, red, amber are used consistently for approved, denied, pending.
8. **Card shadows** — Subtle shadows on cards (`shadow-sm`), not flat boxes.
9. **Typography hierarchy** — Large bold for product name, medium for price, small muted for merchant/timestamp.
10. **Responsive** — Works on different screen sizes (sidebar collapses on mobile). Not critical for demo video but shows polish if judges resize.

---

## PART 2: ADK SHOPPING AGENT

### 2.1 What You're Building

An AI agent using Google ADK + Gemini 2.5 Computer Use that:
- Opens a Playwright browser
- Navigates real e-commerce sites (Amazon, Target)
- Searches for products, compares options
- Calls `request_purchase` before payment (intercepted by plugin)
- Fills checkout form with Argus-issued virtual card if approved
- If denied, automatically searches for alternatives

### 2.2 Setup

```bash
pip install google-adk google-genai playwright
playwright install chromium
```

### 2.3 Agent Definition

Full spec in **argus-data-spec.md Section 5**. Key files:

**agent/shopping_agent/agent.py:**

```python
from google.adk.agents import Agent
from google.adk.toolsets import ComputerUseToolset
from google.adk.toolsets.computer_use import PlaywrightComputer
from agent.argus_plugin.request_purchase import request_purchase
from agent.shopping_agent.prompts import AGENT_INSTRUCTION

shopping_agent = Agent(
    model='gemini-2.5-computer-use-preview-10-2025',
    name='argus_shopping_agent',
    instruction=AGENT_INSTRUCTION,
    tools=[
        ComputerUseToolset(
            computer=PlaywrightComputer(screen_size=(1280, 936))
        ),
        request_purchase,
    ]
)
```

**agent/shopping_agent/prompts.py:**

The full system instruction is in **argus-data-spec.md Section 5.2**. Key points:
- Tell the agent to SEARCH, COMPARE, SELECT, ADD TO CART, then CALL request_purchase BEFORE entering any payment info
- If denied: tell user why and search for alternatives
- If pending approval: tell user it's waiting and poll
- NEVER type card numbers that didn't come from request_purchase

**agent/run_agent.py:**

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent.shopping_agent.agent import shopping_agent
from agent.argus_plugin.plugin import ArgusPlugin

session_service = InMemorySessionService()

runner = Runner(
    agent=shopping_agent,
    app_name="argus_demo",
    session_service=session_service,
    plugins=[ArgusPlugin(
        argus_api_url="http://localhost:8000/api/v1",
        connection_key="argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e"
    )]
)
```

### 2.4 Running the Agent

For development and testing, use ADK Dev UI:
```bash
adk web agent/
```
This opens a chat interface at http://localhost:8080 where you can type messages and watch the agent act.

### 2.5 Agent Testing Strategy

**Test incrementally:**

1. **Basic browsing test:** "Go to amazon.com and search for running shoes" — verify Playwright opens, navigates, searches
2. **Product selection test:** "Find running shoes under $80 on Amazon" — verify agent browses, compares, selects one
3. **request_purchase test:** After agent selects a product, verify it calls request_purchase with correct details (check your API logs)
4. **Full flow test:** Backend running + agent running → agent finds product → calls request_purchase → API evaluates → returns card → agent fills checkout

**Common issues:**
- Gemini Computer Use can be slow (10-30 seconds per action) — be patient
- Amazon may show CAPTCHAs or different layouts — try with a fresh browser profile
- If Amazon blocks Playwright, try Target, Best Buy, or Google Shopping
- Agent may struggle with complex checkout forms — may need prompt tuning

### 2.6 Backup Plan: Pre-Recorded Agent Run

If the agent is unreliable during video recording:
1. Run the demo until you get a successful end-to-end flow
2. Screen record that successful run
3. Use the recording in the pitch video
4. The dashboard side can be shown live since it's stable

---

## PART 3: PITCH & VIDEO

### 3.1 Demo Scenario Script (Option A — One Deep Flow)

**Pre-demo setup:**
- Backend running with seeded data
- Dashboard open in browser, logged in as demo@argus.dev
- Agent ready to launch (ADK Dev UI or custom chat)
- Screen recording software running

**Script:**

```
[Show dashboard — Categories page briefly]
"Argus lets users define spending categories with rules.
 Here we have Footwear: max $200 per transaction, auto-approve
 under $80, daily limit $300, only from whitelisted merchants."

[Switch to agent chat]
"Let's see what happens when our AI agent goes shopping."

[Type: "Find me running shoes under $80"]

[Agent opens browser, navigates to Amazon, searches]
"The agent is browsing Amazon using Gemini Computer Use,
 searching for products that match the user's request."

[Agent finds shoes ~$95, calls request_purchase]
[Switch to dashboard — show transaction appear in real-time]
"The agent found shoes at $95 and submitted a purchase request.
 Argus evaluates: $95 exceeds the $80 auto-approve threshold.
 DENIED."

[Show red DENIED badge on dashboard with reason]
"The dashboard shows the denial in real-time with the reason.
 The agent automatically searches for a cheaper option."

[Agent finds shoes ~$60, calls request_purchase again]
[Dashboard shows new transaction → APPROVED]
"Now the agent found shoes at $60. Argus evaluates: under $80,
 amazon.com is whitelisted, within daily budget. APPROVED."

[Show green APPROVED badge with virtual card details]
"Argus issues a scoped single-use virtual card — locked to
 Amazon, limited to the purchase amount plus tax buffer,
 expires in 30 minutes."

[Agent fills checkout form with virtual card]
"The agent uses ONLY the Argus-issued card to complete checkout.
 It cannot use any other payment method — our plugin blocks
 any card number that Argus didn't authorize."

[Show final dashboard state with both transactions visible]
"Every transaction is logged with full audit trail: which
 category, which rules were checked, Gemini's AI reasoning,
 and the virtual card details."
```

### 3.2 Video Structure (2:30)

```
0:00 - 0:20  HOOK
  "AI agents are about to spend $1.2 trillion on behalf of
   consumers. But right now, if you give an AI agent your credit
   card, there's nothing stopping it from overspending, buying
   the wrong thing, or shopping at merchants you don't trust.
   That's the problem Argus solves."

0:20 - 0:40  SOLUTION (with architecture diagram)
  "Argus is a payment authorization layer for AI agents. When
   an agent wants to buy something, Argus intercepts the request,
   evaluates it against user-defined spending rules using AI-powered
   categorization, and either approves — issuing a scoped virtual
   card — denies with an explanation, or escalates to the user
   for approval in real-time."

0:40 - 2:00  LIVE DEMO (the script above)
  Show the full deny → approve flow

2:00 - 2:15  TECH DIFFERENTIATION
  "Under the hood, Argus uses:
   - Google ADK with Gemini Computer Use for the shopping agent
   - Gemini 2.0 Flash for AI-powered purchase categorization
   - A deterministic rules engine for spending policy enforcement
   - Scoped virtual cards for transaction-level security
   - Google's A2A protocol — meaning any agent on any framework
     can discover and use Argus without custom integration"

2:15 - 2:30  VISION
  "Argus is the Visa network for AI agents. Just as Visa sits
   between every merchant and every cardholder, Argus sits between
   every AI agent and every purchase. As agentic commerce grows
   to a trillion-dollar market, every agent will need a payment
   guardian. We're building that infrastructure."
```

### 3.3 Market Research Data Points (Find These)

For the Market Fit score (1-10), you need real numbers:

| Data Point | Where to Find |
|-----------|---------------|
| Agentic commerce market size projections | Gartner, McKinsey, Statista |
| AI agent deployment numbers (2025-2026) | Industry reports, Google/OpenAI announcements |
| Consumer trust in AI spending | Survey data (Pew, Deloitte) |
| Virtual card market growth | Juniper Research, Grand View Research |
| Fraud in digital commerce | Nilson Report, LexisNexis |
| Credit union pain points | NCUA data, CUNA reports |

**Key stats to find:**
- "AI agentic commerce projected to reach $X trillion by 20XX" → use in video hook
- "X% of consumers don't trust AI agents with their money" → problem statement
- "Virtual card market growing at X% CAGR" → solution validation
- "Average fraud loss per digital transaction: $X" → urgency

### 3.4 Pitch Slides (If Needed)

If you add slides before/after the demo:

1. **Title:** ARGUS — The Payment Guardian for AI Agents (with logo + Argus Panoptes image)
2. **Problem:** AI agents spending money with zero oversight (stat + visual)
3. **Solution:** One-sentence + architecture diagram
4. **Demo:** (this is the screen recording)
5. **Tech:** A2A protocol, Gemini evaluation, virtual card scoping, plugin architecture
6. **Market:** Stats + BankSocial compatibility + credit union angle
7. **Vision:** "Visa for AI agents" + market size + team

Use Canva or Google Slides. Keep it minimal — the demo is the star.

### 3.5 Video Recording Tips

- **Screen recording:** OBS Studio (free, reliable)
- **Resolution:** 1920x1080, 30fps minimum
- **Audio:** Use a decent microphone. Clear narration > fancy visuals.
- **Browser state:** Clean browser window, no personal bookmarks/tabs visible
- **Dashboard:** Have it in a clean state with 0-2 existing transactions before starting
- **Agent window:** Position next to or behind dashboard. May want side-by-side layout.
- **Rehearse 3+ times** before recording
- **Record multiple takes** — pick the best one
- **If agent is flaky:** Pre-record the agent portion, use clean audio narration over it
- **Editing:** CapCut or DaVinci Resolve for trimming, adding transitions, logo overlay

---

## PART 4: PROJECT MANAGEMENT

### 4.1 Integration Checkpoints

These are the moments you and your teammate need to sync:

| When | What | You Need From Teammate | You Provide |
|------|------|----------------------|-------------|
| Hour ~2 | Auth works | POST /login returns JWT | Dashboard can call login endpoint |
| Hour ~4 | Data flows | GET /transactions returns data, WebSocket sends messages | Dashboard displays transactions + real-time updates |
| Hour ~6 | First E2E | POST /evaluate works, Plugin built | Agent calls request_purchase → full flow works |
| Hour ~8 | Approvals | Approve/deny endpoints work | Dashboard approval flow works |
| Hour ~10 | Deploy | Backend on Dockploy | Frontend on Vercel |

### 4.2 Communication Protocol

- **Slack/Discord:** Quick questions, status updates
- **Screen share:** For debugging integration issues
- **Don't block each other:** If an API endpoint isn't ready yet, mock it locally in the frontend (hardcoded data in a mock file). Build UI against the types, swap in real API when ready.

### 4.3 If Behind Schedule — Cut List

Cut in this order:

| Priority | What to Cut | Impact | Fallback |
|----------|-------------|--------|----------|
| 1st cut | A2A endpoint | Loses tech innovation points | Mention in pitch + show on architecture diagram |
| 2nd cut | Categories page | Loses one dashboard page | Show categories inline on dashboard page |
| 3rd cut | Transaction detail page | Loses detailed view | Show key info in the transaction card itself |
| 4th cut | Deploy to cloud | Loses live URL | Demo from localhost, say "deployable architecture" in pitch |
| 5th cut | Custom agent chat | Loses branded agent UI | Use ADK Dev UI (Google's built-in) |

**NEVER CUT:** Transaction feed on dashboard, working agent demo (even pre-recorded), evaluate endpoint, pitch video.

---

## Your Build Order

This is the sequence to maximize progress and unblock yourself:

### Hours 0-2: Foundation
- [ ] Create Vite + React + Tailwind project
- [ ] Install shadcn/ui components
- [ ] Set up React Router (login → protected routes)
- [ ] Build AppLayout (sidebar + header + content slot)
- [ ] Build AppSidebar with nav links
- [ ] Create types.ts with all TypeScript interfaces
- [ ] Create api.ts with axios instance
- [ ] Build LoginPage + LoginForm (even if backend auth isn't ready, build the UI)

### Hours 2-4: Dashboard Core
- [ ] Build useAuth hook (login, logout, token storage)
- [ ] Build StatusBadge component (green/red/amber/blue)
- [ ] Build TransactionCard component
- [ ] Build TransactionFeed component
- [ ] Build DashboardPage (connects feed + WebSocket)
- [ ] Build useWebSocket hook
- [ ] **SYNC with teammate:** Test login end-to-end, test transaction list

### Hours 4-6: Agent + More Pages
- [ ] Set up ADK shopping agent (agent.py, prompts.py, run_agent.py)
- [ ] Test agent browsing (basic navigation test)
- [ ] Build CategoriesPage (read-only list of categories + rules)
- [ ] Build CategoryCard + RuleTag components

### Hours 6-8: Approvals + Integration
- [ ] Build ApprovalQueue + ApprovalDialog
- [ ] Build ApprovalsPage
- [ ] Build TransactionDetailPage
- [ ] **SYNC with teammate:** Full end-to-end test (agent → plugin → API → dashboard)
- [ ] Test approval flow (WebSocket notification → approve button → card issued)

### Hours 8-10: Polish + Agent Reliability
- [ ] Dashboard polish: loading skeletons, empty states, animations
- [ ] Agent reliability testing — run demo scenario multiple times
- [ ] Fix any bugs from integration testing
- [ ] Deploy frontend to Vercel (if backend is deployed)

### Hours 10-12: Demo + Video
- [ ] Demo rehearsal (full scenario, 3+ times)
- [ ] Screen record successful demo
- [ ] Record narration (or narrate live during screen recording)
- [ ] Edit video to 2:30
- [ ] Create Devpost submission
- [ ] Write project description
- [ ] Take screenshots for Devpost
- [ ] Submit

---

## Reference

- **argus-data-spec.md** — Source of truth for ALL API responses, schemas, WebSocket messages
- **argus-project-overview.md** — High-level project context
- **argus-teammate-guide.md** — What your teammate is building (know what to expect from the API)
