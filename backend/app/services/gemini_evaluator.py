import json
import logging
from typing import Optional, List

from app.config import settings

logger = logging.getLogger(__name__)


# ── System instructions ────────────────────────────────────────────────────────

_CALL1_SYSTEM = (
    "You are Argus, a financial transaction intent analyzer. Read the "
    "conversation between a user and their AI shopping agent. Determine "
    "what the user actually wants to buy and which spending category it "
    "falls into.\n\n"
    "IMPORTANT: Focus primarily on the USER's messages to determine intent. "
    "The agent's messages provide context for what actions were taken, but "
    "the user's own words are the ground truth for what they want. If the "
    "agent's messages contradict the user's stated intent, flag this and "
    "trust the user's words.\n\n"
    "Respond with ONLY valid JSON."
)

_CALL2_SYSTEM = (
    "You are Argus, a financial transaction decision-maker. You are given "
    "a full evaluation report containing: what the user wanted (intent), "
    "what category was determined, what the agent claims it's buying "
    "(product details), and what the spending rules say.\n\n"
    "Your job is to cross-reference all of this and make a decision:\n"
    "  APPROVE  — everything checks out, transaction is safe\n"
    "  DENY     — clear misalignment or risk that justifies blocking\n"
    "  HUMAN_NEEDED — uncertain, ambiguous, or borderline — let the user decide\n\n"
    "KEY CROSS-CHECKS TO PERFORM:\n"
    "1. Does the product match what the user asked for?\n"
    "   (shoes vs gift card = mismatch → flag it)\n"
    "2. Does the price align with the user's budget?\n"
    "   ($120 when user said \"under $80\" → flag it)\n"
    "3. Is the merchant trustworthy?\n"
    "4. Are there signs of agent drift or manipulation?\n"
    "   (agent buying something completely different from user intent)\n\n"
    "CUSTOM RULES: If custom rules are provided, evaluate each one against "
    "the product details and context. Return pass/fail with reasoning. "
    "If a custom rule fails, recommend HUMAN_NEEDED (not DENY — these are "
    "judgment calls that deserve human review).\n\n"
    "Be CONSERVATIVE: when in doubt, choose HUMAN_NEEDED over APPROVE. "
    "False approvals are worse than false escalations.\n\n"
    "Respond with ONLY valid JSON."
)


# ── Prompt builders ────────────────────────────────────────────────────────────

def _build_call1_prompt(chat_history: str, categories: list) -> str:
    """Build Call 1 prompt — only chat_history + categories (NO product details)."""
    categories_json = json.dumps(
        [{"name": c["name"], "description": c.get("description", ""),
          **({"is_default": True} if c.get("is_default") else {})} for c in categories],
        indent=2
    )
    return f"""## Conversation History
{chat_history}

## Available Spending Categories
{categories_json}

## Return JSON:
{{
  "intent": {{
    "want": "<what the user wants to buy>",
    "budget": "<budget constraint or 'not specified'>",
    "preferences": "<brand, quality, or other preferences>",
    "urgency": "<normal | urgent | not specified>",
    "summary": "<one sentence combining all of the above>"
  }},
  "category": {{
    "name": "<EXACT name from categories list>",
    "confidence": <0.0-1.0>,
    "reasoning": "<why this category fits the user's intent>"
  }}
}}"""


def _build_call2_prompt(report: dict, custom_rules: list) -> str:
    """Build Call 2 prompt — full report + custom rules."""
    report_json = json.dumps(report, indent=2)
    custom_rules_json = json.dumps(custom_rules, indent=2) if custom_rules else "None"
    return f"""## Full Evaluation Report
{report_json}

## Custom Rules to Evaluate
{custom_rules_json}

## Return JSON:
{{
  "decision": "<APPROVE | DENY | HUMAN_NEEDED>",
  "reasoning": "<2-3 sentences explaining your decision>",
  "confidence": <0.0-1.0>,
  "risk_flags": [<list of plain-language risk descriptions, or empty>],
  "intent_match": <0.0-1.0 — how well does the product match intent>,
  "custom_rule_results": [
    {{
      "rule_id": "<id>",
      "passed": <true/false>,
      "detail": "<why it passed or failed>"
    }}
  ]
}}"""


# ── Mock/fallback responses ────────────────────────────────────────────────────

def _mock_call1_response(categories: list) -> dict:
    """
    Stub response for Call 1 — used when no API key or Gemini fails.
    Returns the default category at high confidence with generic intent.
    """
    default_cat = next((c for c in categories if c.get("is_default")), None)
    category_name = default_cat["name"] if default_cat else (categories[0]["name"] if categories else "General")
    return {
        "intent": {
            "want": "Unknown (AI evaluation unavailable)",
            "budget": "not specified",
            "preferences": "not specified",
            "urgency": "not specified",
            "summary": "[MOCK] Gemini unavailable. Intent not extracted.",
        },
        "category": {
            "name": category_name,
            "confidence": 0.90,
            "reasoning": "[MOCK] Default category assigned — Gemini not configured or failed.",
        },
    }


def _mock_call2_response() -> dict:
    """
    Conservative fallback for Call 2 — always returns HUMAN_NEEDED.
    Never auto-approve without AI confirmation.
    """
    return {
        "decision": "HUMAN_NEEDED",
        "reasoning": "[MOCK] Gemini unavailable for final decision. Falling back to human review.",
        "confidence": 0.0,
        "risk_flags": ["ai_evaluation_degraded"],
        "intent_match": 0.5,
        "custom_rule_results": [],
    }


# ── Gemini Call 1: Extract Intent + Category ───────────────────────────────────

async def extract_intent_and_category(chat_history: str, categories: list) -> dict:
    """
    GEMINI CALL 1: Extract user intent and determine category from chat history.

    Security: This call intentionally receives NO product details — only the
    conversation and category definitions. Category assignment comes from the
    user's own words, not from what the agent claims.

    Returns: {intent: {...}, category: {name, confidence, reasoning}}
    Fallback: _mock_call1_response() (default category, 0.90 confidence)
    """
    if not settings.google_api_key:
        logger.info("No GOOGLE_API_KEY — returning mock Call 1 response")
        return _mock_call1_response(categories)

    prompt = _build_call1_prompt(chat_history, categories)

    for attempt in range(2):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_eval_model,
                system_instruction=_CALL1_SYSTEM,
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)

            # Validate required structure
            if "intent" in result and "category" in result:
                result["intent"].setdefault("want", "unknown")
                result["intent"].setdefault("budget", "not specified")
                result["intent"].setdefault("preferences", "not specified")
                result["intent"].setdefault("urgency", "not specified")
                result["intent"].setdefault("summary", "unknown")
                result["category"].setdefault("confidence", 0.5)
                result["category"].setdefault("reasoning", "")
                logger.info(f"Gemini Call 1 succeeded on attempt {attempt + 1}")
                return result

            logger.warning(f"Gemini Call 1 attempt {attempt + 1}: missing intent/category keys")

        except Exception as e:
            logger.warning(f"Gemini Call 1 attempt {attempt + 1} failed: {e}")

    logger.warning("Gemini Call 1 failed after 2 attempts — returning mock response")
    return _mock_call1_response(categories)


# ── Gemini Call 2: Make Final Decision ─────────────────────────────────────────

async def make_final_decision(report: dict, custom_rules: list = None) -> dict:
    """
    GEMINI CALL 2: Given full report (intent + category + product + rules),
    cross-check everything and make a final decision.

    Only called when rules_outcome is NOT HARD_DENY.

    Returns: {decision, reasoning, confidence, risk_flags, intent_match, custom_rule_results}
    Fallback: conservative HUMAN_NEEDED (never auto-approve blind)
    """
    if not settings.google_api_key:
        logger.info("No GOOGLE_API_KEY — returning mock Call 2 response (HUMAN_NEEDED)")
        return _mock_call2_response()

    prompt = _build_call2_prompt(report, custom_rules or [])

    for attempt in range(2):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_eval_model,
                system_instruction=_CALL2_SYSTEM,
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)

            # Validate required structure
            required = ["decision", "reasoning", "confidence", "risk_flags", "intent_match"]
            if all(k in result for k in required):
                result.setdefault("custom_rule_results", [])
                # Validate decision value
                if result["decision"] not in ("APPROVE", "DENY", "HUMAN_NEEDED"):
                    result["decision"] = "HUMAN_NEEDED"
                    result["risk_flags"].append("AI returned invalid decision — defaulting to HUMAN_NEEDED")
                logger.info(f"Gemini Call 2 succeeded on attempt {attempt + 1}: decision={result['decision']}")
                return result

            logger.warning(f"Gemini Call 2 attempt {attempt + 1}: missing required fields")

        except Exception as e:
            logger.warning(f"Gemini Call 2 attempt {attempt + 1} failed: {e}")

    logger.warning("Gemini Call 2 failed after 2 attempts — returning conservative HUMAN_NEEDED")
    return _mock_call2_response()
