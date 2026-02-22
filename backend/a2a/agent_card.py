import os


def get_agent_card() -> dict:
    """
    Returns the Argus Agent Card — the A2A discovery document.
    Served at GET /.well-known/agent.json so any A2A-compatible agent
    can discover Argus and learn how to call it.

    The base URL is read from ARGUS_PUBLIC_URL env var so it works in
    both local dev (localhost:8000) and production (deployed URL).
    """
    base_url = os.getenv("ARGUS_PUBLIC_URL", "http://localhost:8000").rstrip("/")

    return {
        "name": "Argus Payment Guardian",
        "description": (
            "AI agent payment authorization system. Evaluates purchase requests "
            "against user-defined spending rules and issues scoped virtual cards "
            "for approved transactions."
        ),
        "url": f"{base_url}/a2a",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "skills": [
            {
                "id": "evaluate_purchase",
                "name": "Evaluate Purchase",
                "description": (
                    "Submit a purchase request for authorization. Argus evaluates it "
                    "against the user's spending rules and returns one of: "
                    "APPROVE (with virtual card details), DENY (with reason), or "
                    "HUMAN_NEEDED (poll /transactions/{id}/status for the outcome). "
                    "Providing chat_history improves intent detection accuracy."
                ),
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
                "inputSchema": {
                    "type": "object",
                    "required": ["product_name", "price", "merchant_name", "merchant_url"],
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Exact name of the product being purchased.",
                        },
                        "price": {
                            "type": "number",
                            "description": "Exact price at checkout in USD.",
                        },
                        "merchant_name": {
                            "type": "string",
                            "description": "Name of the store or merchant.",
                        },
                        "merchant_url": {
                            "type": "string",
                            "description": "Full URL of the checkout page.",
                        },
                        "product_url": {
                            "type": "string",
                            "description": "URL of the product detail page (optional).",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Extra context: color, size, reason for selection (optional).",
                        },
                        "chat_history": {
                            "type": "string",
                            "description": (
                                "Conversation history between user and agent formatted as "
                                "'User: ...\\nAgent: ...\\n'. Recommended — used by Argus to "
                                "extract user intent for more accurate authorization decisions."
                            ),
                        },
                    },
                },
            }
        ],
        "authentication": {
            "schemes": ["bearer"],
            "description": "Pass a valid Argus connection key as: Authorization: Bearer argus_ck_...",
        },
    }
