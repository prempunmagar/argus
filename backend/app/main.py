from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from seed import seed as run_seed
from app.routers import auth, health
from app.routers import evaluate as evaluate_router
from app.routers import transactions as transactions_router
from app.routers import categories as categories_router
from app.routers import profiles as profiles_router
from app.routers import connection_keys as connection_keys_router
from app.routers import payment_methods as payment_methods_router
from a2a.handler import router as a2a_router
from app.services.auth_service import decode_jwt
from app.services.websocket_manager import ws_manager

# --- Create the FastAPI app ---
app = FastAPI(
    title="Argus Core API",
    version="1.0.0",
    description="AI Agent Payment Authorization System",
)

# --- CORS middleware ---
# Allows Prem's React frontend (localhost:5173) to call our API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers ---
# Auth endpoints: POST /api/v1/auth/register, POST /api/v1/auth/login
app.include_router(auth.router, prefix="/api/v1")

# Evaluate endpoint: POST /api/v1/evaluate
app.include_router(evaluate_router.router, prefix="/api/v1")

# Transaction endpoints: GET /api/v1/transactions, GET /api/v1/transactions/{id}, GET /api/v1/transactions/{id}/status
app.include_router(transactions_router.router, prefix="/api/v1")

# Categories endpoints: GET/POST /api/v1/categories, PUT /api/v1/categories/{id}
app.include_router(categories_router.router, prefix="/api/v1")

# Profiles: GET/POST /api/v1/profiles, PUT /api/v1/profiles/{id}
app.include_router(profiles_router.router, prefix="/api/v1")

# Connection keys: GET/POST /api/v1/connection-keys, DELETE /api/v1/connection-keys/{id}
app.include_router(connection_keys_router.router, prefix="/api/v1")

# Payment methods: GET/POST /api/v1/payment-methods
app.include_router(payment_methods_router.router, prefix="/api/v1")

# Health endpoint: GET /health (no /api/v1 prefix — standard practice)
app.include_router(health.router)

# A2A endpoints: GET /.well-known/agent.json, POST /a2a (no prefix — A2A spec requires root paths)
app.include_router(a2a_router)


# --- WebSocket: /ws/dashboard ---
# Dashboard connects here to receive real-time transaction updates.
# Auth: JWT passed as ?token=eyJ... query parameter.
@app.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(...),
):
    payload = decode_jwt(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # Keep the connection alive; the server only sends, never receives
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)



# --- Startup event ---
# Creates all database tables on first run. SQLAlchemy checks if they exist
# before creating, so this is safe to run every time.
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    run_seed()
