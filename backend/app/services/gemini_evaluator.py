import json
import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

# Configure the Gemini SDK with our API key.
# If the key is empty, Gemini calls will fail and we'll use the keyword fallback.
if settings.google_api_key:
    genai.configure(api_key=settings.google_api_key)

# ------------------------------------------------------------------
# System prompt — copied exactly from argus-data-spec.md Section 9.1
# ------------------------------------------------------------------
SYSTEM_PROMPT = """You are Argus, a financial transaction evaluator for an AI agent \
payment authorization system. An AI shopping agent wants to make \
a purchase on behalf of a user. Your job is:

1. Determine which of the user's spending categories this purchase \
   belongs to
2. Evaluate how well the purchase matches the user's stated intent
3. Flag any risk concerns

You must respond with ONLY a valid JSON object. No markdown, no \
explanation, no backticks. Just the JSON."""


def _build_user_prompt(
    categories_json: str,
    product_name: str,
    price: float,
    currency: str,
    merchant_name: str,
    merchant_url: str,
    conversation_context: str | None,
) -> str:
    """Build the user prompt from the template in argus-data-spec.md Section 9.1."""
    context = conversation_context or "No conversation context provided."

    return f"""## User's Spending Categories

{categories_json}

## Purchase Request

Product: {product_name}
Price: {price} {currency}
Merchant: {merchant_name}
Merchant URL: {merchant_url}

## Conversation Context

{context}

## Instructions

Return a JSON object with exactly these fields:

{{
  "category_name": "EXACT name from the categories list above that best matches this purchase. If no category is a confident match, use the category marked as default.",
  "category_confidence": <float 0.0-1.0, how confident you are in the category match>,
  "intent_match": <float 0.0-1.0, how well the purchase matches what the user asked for based on the conversation context>,
  "intent_summary": "<one sentence explaining how the purchase relates to the user's request>",
  "risk_flags": [<list of string flags, empty if no concerns>],
  "reasoning": "<2-3 sentences explaining your overall assessment>"
}}

Valid risk_flags values:
- "price_exceeds_stated_budget" — user said a budget, price is over it
- "product_category_mismatch" — product doesn't match what user asked for
- "possible_upsell" — agent picked premium when user wanted basic
- "merchant_suspicious" — merchant domain looks unusual or mimics a known brand
- "intent_unclear" — not enough context to evaluate match
- "luxury_item_on_budget_request" — user wanted budget option, agent picked luxury
- "subscription_not_requested" — agent is signing up for recurring charge
- "different_brand_than_requested" — user specified brand, agent chose different
- "multiple_items_unexpected" — user asked for one item, cart has multiple"""


def _categories_to_json(categories) -> str:
    """
    Convert a list of SpendingCategory SQLAlchemy objects into the JSON
    format that Gemini expects. Keywords are stored as a JSON string in
    the database, so we parse them back into a list.
    """
    return json.dumps(
        [
            {
                "name": c.name,
                "description": c.description or "",
                "keywords": json.loads(c.keywords) if c.keywords else [],
                "is_default": c.is_default,
            }
            for c in categories
        ],
        indent=2,
    )


async def evaluate_purchase(
    categories,
    product_name: str,
    price: float,
    currency: str,
    merchant_name: str,
    merchant_url: str,
    conversation_context: str | None,
) -> dict:
    """
    Call Gemini 2.0 Flash for category detection + risk assessment.

    Retry once on failure, then fall back to keyword-based categorization.

    Args:
        categories: list of SpendingCategory objects (user's categories)
        product_name, price, currency, merchant_name, merchant_url: purchase info
        conversation_context: the agent's conversation with the user

    Returns:
        dict with keys: category_name, category_confidence, intent_match,
        intent_summary, risk_flags, reasoning
    """
    # If no API key configured, go straight to fallback
    if not settings.google_api_key:
        logger.warning("No GOOGLE_API_KEY configured — using keyword fallback")
        return keyword_fallback(categories, product_name)

    categories_json = _categories_to_json(categories)
    user_prompt = _build_user_prompt(
        categories_json, product_name, price, currency,
        merchant_name, merchant_url, conversation_context,
    )

    model = genai.GenerativeModel(
        model_name=settings.gemini_eval_model,
        system_instruction=SYSTEM_PROMPT,
    )

    # First attempt
    try:
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        logger.info("Gemini evaluation succeeded on first attempt")
        return result
    except Exception as e:
        logger.warning(f"Gemini first attempt failed: {e}")

    # Retry once
    try:
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        logger.info("Gemini evaluation succeeded on retry")
        return result
    except Exception as e:
        logger.warning(f"Gemini retry also failed: {e} — using keyword fallback")
        return keyword_fallback(categories, product_name)


def keyword_fallback(categories, product_name: str) -> dict:
    """
    Fallback when Gemini is unavailable.

    Tries to match the product name against each category's keywords.
    If no keyword matches, falls back to the user's default category.
    """
    product_lower = product_name.lower()

    # Try to match by keywords
    for cat in categories:
        keywords = json.loads(cat.keywords) if cat.keywords else []
        if any(kw.lower() in product_lower for kw in keywords):
            return {
                "category_name": cat.name,
                "category_confidence": 0.5,
                "intent_match": 0.5,
                "intent_summary": "Matched by keyword (AI evaluation degraded)",
                "risk_flags": ["ai_evaluation_degraded"],
                "reasoning": "Gemini was unavailable. Matched by keyword.",
            }

    # No keyword match — use default category
    default = next((c for c in categories if c.is_default), categories[0])
    return {
        "category_name": default.name,
        "category_confidence": 0.3,
        "intent_match": 0.5,
        "intent_summary": "No category match (AI evaluation degraded)",
        "risk_flags": ["ai_evaluation_degraded", "intent_unclear"],
        "reasoning": "Gemini was unavailable. No keyword match. Using default category.",
    }
