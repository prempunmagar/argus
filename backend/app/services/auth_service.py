from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing setup.
# bcrypt is a one-way hash — you can verify a password against the hash,
# but you can never reverse the hash back to the original password.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain text password. Used during registration."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain text password matches a hashed one. Used during login."""
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt(user_id: str, email: str) -> str:
    """
    Create a JWT token for a user.
    The token contains:
      - sub: the user's ID (who this token belongs to)
      - email: for convenience
      - exp: when the token expires
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def decode_jwt(token: str) -> dict | None:
    """
    Decode and validate a JWT token.
    Returns the payload dict if valid, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
