# Argus — The Payment Guardian for AI Agents

> The Visa network for AI agents — every purchase goes through us, and we make sure it's the right one.

Argus is an AI agent payment authorization system that intercepts AI shopping agent purchases, evaluates them against user-defined spending rules using Gemini AI, and issues scoped virtual cards for approved transactions.

Built for the **LIVE AI Ivy Plus Hackathon 2026**.

---

## How It Works

1. Your AI agent browses real e-commerce sites and finds a product to buy
2. Before paying, the agent sends the purchase details to Argus
3. Argus evaluates the purchase — AI categorization + deterministic spending rules
4. Based on the rules:
   - **Approved** — Argus issues a one-time virtual card locked to that merchant and amount
   - **Denied** — The agent gets a reason and can look for alternatives
   - **Needs Approval** — You get a real-time notification on the dashboard to decide
5. The agent completes checkout with the scoped virtual card

The agent never touches your real credit card. Every purchase goes through Argus.

---

## Architecture

| Component | Description |
|-----------|-------------|
| **Core API** | FastAPI backend — receives purchase requests, runs AI categorization + rules, issues virtual cards |
| **Dashboard** | React web UI — real-time transaction feed, approve/deny flagged purchases, configure spending rules |
| **Shopping Agent** | Google ADK + Gemini Computer Use — browses real e-commerce sites with a real browser |
| **ADK Plugin** | Middleware inside the agent that intercepts purchases and routes them through Argus |

---

## Tech Stack

- **Backend:** Python / FastAPI / SQLite
- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui
- **Agent:** Google ADK + Gemini 2.5 Computer Use
- **AI Evaluation:** Gemini 2.0 Flash
- **Virtual Cards:** Mock issuer (realistic, no real money)

---

## Project Structure

```
argus/
├── frontend/          # React dashboard (Vite + Tailwind + shadcn/ui)
│   ├── src/
│   │   ├── components/    # UI components (layout, transactions, categories, etc.)
│   │   ├── pages/         # Route pages (Dashboard, Categories, Approvals, etc.)
│   │   ├── hooks/         # React hooks (useAuth, useProfile, useWebSocket, etc.)
│   │   └── lib/           # Types, API client, utilities, mock data
│   └── package.json
├── backend/           # FastAPI server, database, API endpoints
├── agent/
│   ├── shopping_agent/    # ADK shopping agent (Gemini Computer Use)
│   └── run_agent.py       # Agent entry point
└── argus-data-spec.md     # API contracts, DB schema, WebSocket messages
```

---

## Getting Started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard runs at `http://localhost:5173`. Without a backend, it uses mock data automatically.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Demo Credentials

```
Email: demo@argus.dev
Password: argus2026
```

---

## Demo Scenarios

| Category | Behavior |
|----------|----------|
| **Footwear** | Auto-approves under $80, blocks unknown merchants |
| **Electronics** | Auto-approves under $100, caps at $500/item |
| **Travel** | Always requires human approval |
| **General** | Catch-all with conservative limits |
