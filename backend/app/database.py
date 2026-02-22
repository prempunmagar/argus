from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create the SQLAlchemy engine
# check_same_thread=False is required for SQLite with FastAPI
# because FastAPI handles requests across multiple threads,
# but SQLite by default only allows access from the thread that created it.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# SessionLocal is a factory that creates new database sessions.
# Each request gets its own session, which is closed when the request is done.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all our database models.
# Every model (User, Transaction, etc.) will inherit from this.
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session to each request.
    Used like: db: Session = Depends(get_db)

    The 'yield' makes this a generator — FastAPI will:
    1. Call next() to get the session (before the route runs)
    2. Let the route use the session
    3. Call next() again to hit the 'finally' block (after the route finishes)
    This guarantees the session is always closed, even if the route crashes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
