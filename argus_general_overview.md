# Argus — The Payment Guardian for AI Agents

## 👋 Welcome

This doc gives you a quick, plain-English overview of what Argus is, why it matters, and how it works. If you're thinking about joining the team or just want to understand the project, start here.

---

## The Problem

AI agents are starting to shop on our behalf — browsing Amazon, comparing products, adding to cart, and checking out. But right now, if you give an agent your credit card, there are **zero guardrails**. No spending limits, no merchant restrictions, no way to say "ask me first if it's over $100."

That's a massive trust gap. And as agentic commerce scales toward a trillion-dollar market, someone needs to build the control layer.

---

## What Argus Does

Argus sits between an AI shopping agent and your money. Think of it as a **smart approval layer** — like a corporate expense policy, but for your personal AI assistant.

Here's the simple version of what happens:

1. **You tell your AI agent:** "Buy me running shoes under $80"
2. **The agent browses real sites** (Amazon, Target, etc.), picks a product, and heads to checkout
3. **Before paying, the agent checks with Argus** — sending the product name, price, and merchant
4. **Argus evaluates the purchase** against your rules:
   - Is it within budget for this category?
   - Is this merchant allowed?
   - Does this need your manual approval?
5. **Based on the rules:**
   - ✅ **Approved** → Argus issues a one-time virtual card locked to that merchant and amount
   - ❌ **Denied** → The agent gets a reason and can look for alternatives
   - 🔔 **Needs Approval** → You get a notification on the dashboard and decide in real-time
6. **The agent completes checkout** with the scoped virtual card

The key insight: the agent never touches your real credit card. Every purchase goes through Argus.

---

## The One-Liner

> **Argus is the Visa network for AI agents — every purchase goes through us, and we make sure it's the right one.**

---

## What We're Building

| Component | What It Does |
|-----------|-------------|
| **Core API** | The brain — receives purchase requests, runs AI categorization + rules, issues virtual cards |
| **Shopping Agent** | An AI agent (Google ADK + Gemini) that browses real e-commerce sites using a real browser |
| **Dashboard** | A web UI where users see transactions in real-time, approve/deny flagged purchases, and configure spending rules |
| **ADK Plugin** | Middleware inside the agent that intercepts purchases and routes them through Argus |

---

## Tech Stack at a Glance

- **Backend:** Python / FastAPI
- **Frontend:** React + Tailwind + shadcn/ui
- **Agent:** Google ADK with Gemini (computer use model)
- **AI Evaluation:** Gemini 2.0 Flash for categorizing purchases
- **Database:** SQLite (lightweight, no infra needed)
- **Virtual Cards:** Mock issuer (realistic but no real money moves)

---

## Demo Scenarios

We have preset spending categories to showcase different behaviors:

| Category | What Happens |
|----------|-------------|
| **Footwear** | Auto-approves under $80, blocks unknown merchants |
| **Electronics** | Auto-approves under $100, caps at $500/item |
| **Travel** | Always requires human approval (no auto-approve) |
| **General** | Catch-all with conservative limits |

---

## Why It's Interesting

- **Real integrations** — not mock UIs. The agent browses actual websites with a real browser.
- **AI + Rules hybrid** — Gemini categorizes purchases intelligently, then deterministic rules enforce policy. Best of both worlds.
- **Human-in-the-loop** — the dashboard gives users real-time control over what gets approved.
- **Scoped virtual cards** — each approved purchase gets a single-use card locked to that merchant and amount. Even if something goes wrong, exposure is minimal.

---

## Hackathon Context

- **Event:** LIVE AI Ivy Plus Hackathon 2026
- **Deliverables:** Working demo, 2-3 minute pitch video, GitHub repo
- **Judging criteria:** UI/UX, tech innovation, code quality, pitch quality, market fit, disruptive potential

---

## The Name

Argus Panoptes was the all-seeing giant of Greek mythology, covered in a hundred eyes that never all closed at once. Our Argus watches every AI agent transaction with the same vigilance. 👁️