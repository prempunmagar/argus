from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, health

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

# Health endpoint: GET /health (no /api/v1 prefix — standard practice)
app.include_router(health.router)


# --- Startup event ---
# Creates all database tables on first run. SQLAlchemy checks if they exist
# before creating, so this is safe to run every time.
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
