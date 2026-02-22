from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """Basic health check. Returns 200 if the server is running."""
    return {"status": "ok", "service": "argus-core"}
