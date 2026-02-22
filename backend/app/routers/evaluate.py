import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AgentContext, get_connection_key_context
from app.schemas.evaluate import EvaluateRequest, EvaluateResponse
from app.services.evaluate_service import run_evaluate_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(
    request: EvaluateRequest,
    agent_ctx: AgentContext = Depends(get_connection_key_context),
    db: Session = Depends(get_db),
):
    """
    POST /evaluate — The core evaluation pipeline.

    Auth: Connection key (argus_ck_...)
    Called by: ADK plugin / shopping agent

    Delegates to evaluate_service.run_evaluate_pipeline() which implements
    the 5-phase / 14-step pipeline (Gemini Call 1 → Rules → Gemini Call 2 → Execute).
    """
    try:
        return await run_evaluate_pipeline(
            request=request,
            user_id=agent_ctx.user_id,
            profile_id=agent_ctx.profile_id,
            connection_key_id=agent_ctx.connection_key_id,
            db=db,
        )
    except Exception as e:
        logger.error(f"Evaluate pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
