from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from app.core.security import verify_access_token
from app.core.config import settings
from app.db.session import db
from app.models.domain import User

def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    Extracts and validates the authenticated user from the Bearer token.
    Enforces a strict authentication boundary: unauthenticated requests are rejected.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Expected 'Authorization: Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1].strip()

    # 1. Standard HS256 JWT signature and expiration verification
    payload = verify_access_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            user = db.users.get(user_id)
            if not user:
                user = db.get_or_create_user({
                    "id": user_id,
                    "email": payload.get("email", f"{user_id}@vertifarm.io"),
                    "name": payload.get("name", "VertiFarm Grower"),
                    "role": payload.get("role", "Farm Owner"),
                })
            return user

    # 2. Development-only token fallback (enabled only when ALLOW_DEV_AUTH=True)
    if settings.ALLOW_DEV_AUTH:
        if token.startswith("dev-token-") or token == "test-token" or token == "mock-token":
            user_id = token.replace("dev-token-", "") if token.startswith("dev-token-") else "usr-default"
            user = db.users.get(user_id)
            if not user:
                user = db.get_or_create_user({
                    "id": user_id,
                    "email": f"{user_id}@vertifarm.io",
                    "name": "Dev Grower",
                    "role": "Farm Owner",
                })
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
