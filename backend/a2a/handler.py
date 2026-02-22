import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from a2a.agent_card import get_agent_card
from app.database import get_db
from app.dependencies import AgentContext, get_connection_key_context
from app.schemas.evaluate import EvaluateRequest, ProductInfo
from app.services.evaluate_service import run_evaluate_pipeline

router = APIRouter()


@router.get("/.well-known/agent.json", tags=["a2a"])
async def agent_card():
    """
    A2A discovery endpoint. Returns the Argus Agent Card so any
    A2A-compatible agent can find Argus and learn its capabilities.
    No authentication required — this is a public discovery document.
    """
    return get_agent_card()


@router.post("/a2a", tags=["a2a"])
async def handle_a2a(
    body: dict,
    agent_context: AgentContext = Depends(get_connection_key_context),
    db: Session = Depends(get_db),
):
    """
    A2A task handler. Accepts JSON-RPC 2.0 tasks/send requests from
    external agents and runs them through the same evaluate pipeline
    as POST /api/v1/evaluate.

    Expected request shape:
    {
        "jsonrpc": "2.0",
        "id": "...",
        "method": "tasks/send",
        "params": {
            "id": "task-123",
            "message": {
                "role": "user",
                "parts": [
                    {"type": "data", "data": {product fields}},
                    {"type": "text", "text": "chat history string"}  // optional
                ]
            }
        }
    }
    """
    rpc_id = body.get("id", str(uuid.uuid4()))
    method = body.get("method")

    # --- JSON-RPC method validation ---
    if method != "tasks/send":
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: '{method}'. Only 'tasks/send' is supported.",
                },
            },
        )

    params = body.get("params", {})
    task_id = params.get("id", str(uuid.uuid4()))
    message = params.get("message", {})
    parts = message.get("parts", [])

    # --- Extract product data and chat history from parts ---
    product_data = {}
    chat_history = ""

    for part in parts:
        if part.get("type") == "data":
            product_data = part.get("data", {})
        elif part.get("type") == "text":
            chat_history = part.get("text", "")

    # --- Validate required product fields ---
    required_fields = ["product_name", "price", "merchant_name", "merchant_url"]
    missing = [f for f in required_fields if not product_data.get(f)]
    if missing:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32602,
                    "message": f"Missing required fields in data part: {', '.join(missing)}",
                },
            },
        )

    # --- Build EvaluateRequest — same schema as POST /api/v1/evaluate ---
    eval_request = EvaluateRequest(
        product=ProductInfo(
            product_name=str(product_data["product_name"]),
            price=float(product_data["price"]),
            merchant_name=str(product_data["merchant_name"]),
            merchant_url=str(product_data["merchant_url"]),
            product_url=product_data.get("product_url"),
            notes=product_data.get("notes"),
        ),
        chat_history=chat_history,
    )

    # --- Run the evaluate pipeline (same logic as POST /evaluate) ---
    result = await run_evaluate_pipeline(
        request=eval_request,
        user_id=agent_context.user_id,
        profile_id=agent_context.profile_id,
        connection_key_id=agent_context.connection_key_id,
        db=db,
    )

    # --- Wrap result in A2A task response format ---
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "parts": [
                        {
                            "type": "data",
                            "data": result.dict(),
                        }
                    ]
                }
            ],
        },
    }
