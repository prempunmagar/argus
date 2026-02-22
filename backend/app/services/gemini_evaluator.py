import json
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# System instruction — spec Section 9.1
_SYSTEM_INSTRUCTION = (
    "You are Argus, a financial transaction evaluator. An AI shopping "
    "agent wants to make a purchase. Determine the category, evaluate intent "
    "match, flag risks, and evaluate any custom rules. Respond with ONLY valid JSON."
)


def _build_prompt(
    categories: list,
    product_name: str,
    price: float,
    currency: str,
    merchant_name: str,
    merchant_url: str,
    conversation_context: Optional[str],
    custom_rules: list,
) -> str:
    """Build evaluation prompt exactly as defined in spec Section 9.1."""
    categories_json = json.dumps(categories, indent=2)
    custom_rules_json = json.dumps(custom_rules, indent=2)
    context = conversation_context or "No conversation context provided."

    return f"""## User's Spending Categories
{categories_json}

## Purchase Request
Product: {product_name}
Price: {price} {currency}
Merchant: {merchant_name} ({merchant_url})

## Conversation Context
{context}

## Custom Rules to Evaluate
{custom_rules_json}
(Each custom rule has an id and a natural-language condition. Evaluate whether \
the purchase satisfies each condition. Return pass/fail with reasoning.)

## Return JSON:
{{
  "category_name": "EXACT name from categories list",
  "category_confidence": <0.0-1.0>,
  "intent_match": <0.0-1.0>,
  "intent_summary": "<one sentence>",
  "risk_flags": [<list of plain-language risk descriptions, or empty>],
  "reasoning": "<2-3 sentences>",
  "custom_rule_results": [
    {{
      "rule_id": "<id of the custom rule>",
      "passed": <true/false>,
      "detail": "<why it passed or failed>"
    }}
  ]
}}

Risk flags should be free-text descriptions of any concerns, e.g.:
- "Price $120 exceeds user's stated budget of under $100"
- "Product is headphones but user asked for shoes"
- "Merchant domain appears suspicious or newly registered"
Return an empty array if no risks are detected.

If no custom rules are provided, return an empty array for custom_rule_results."""


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
        "reasoning": "[MOCK] No GOOGLE_API_KEY configured. Returning stub response for local testing.",
        "custom_rule_results": [],
    }


def call_gemini(
    categories: list,
    product_name: str,
    price: float,
    currency: str,
    merchant_name: str,
    merchant_url: str,
    conversation_context: Optional[str],
    custom_rules: list,
) -> dict:
    """
    Call Gemini 2.0 Flash for category detection + risk evaluation.
    Retries once on failure. Returns a mock stub if no API key is configured
    or if both attempts fail.

    categories: list of dicts with name, description, keywords, is_default
    custom_rules: list of dicts with id, prompt (for CUSTOM_RULE type rules)
    """
    if not settings.google_api_key:
        logger.info("No GOOGLE_API_KEY configured — returning mock response for testing")
        return _mock_response(product_name, categories)

    prompt = _build_prompt(
        categories, product_name, price, currency,
        merchant_name, merchant_url, conversation_context, custom_rules,
    )

    for attempt in range(2):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_eval_model,
                system_instruction=_SYSTEM_INSTRUCTION,
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            result = json.loads(response.text)

            required = [
                "category_name", "category_confidence", "intent_match",
                "intent_summary", "risk_flags", "reasoning",
            ]
            if all(k in result for k in required):
                result.setdefault("custom_rule_results", [])
                logger.info(f"Gemini succeeded on attempt {attempt + 1}")
                return result

            logger.warning(f"Gemini attempt {attempt + 1}: response missing required fields")

        except Exception as e:
            logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")

    logger.warning("Gemini failed after 2 attempts — returning mock response")
    return _mock_response(product_name, categories)
