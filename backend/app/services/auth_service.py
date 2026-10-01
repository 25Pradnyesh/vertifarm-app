from typing import Dict, Any, Optional
from app.core.security import verify_google_id_token, create_access_token
from app.db.session import db
from app.models.domain import User
from app.schemas.user import AuthUser
from app.schemas.auth import TokenResponse

class AuthService:
    def authenticate_google_token(self, id_token_str: str) -> TokenResponse:
        """
        Validates Google ID Token, retrieves/creates user, and issues a JWT session token.
        """
        claims = verify_google_id_token(id_token_str)
        user = db.get_or_create_user({
            "id": claims["id"],
            "email": claims["email"],
            "name": claims["name"],
            "picture": claims.get("picture"),
            "google_id": claims.get("google_id"),
            "auth_provider": "google",
        })

        token_payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        }
        access_token = create_access_token(token_payload)

        auth_user = AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            farmName=user.farm_name,
            avatarUrl=user.avatar_url,
            authProvider=user.auth_provider,
            googleId=user.google_id,
            accessToken=access_token,
            createdAt=user.created_at,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,
            user=auth_user,
        )

    def login_with_email(self, email: str, password: Optional[str] = None) -> TokenResponse:
        """
        Authenticates or provisions user via email (for development and operator login).
        """
        user_id = f"usr-email-{abs(hash(email)) % 1000000}"
        display_name = email.split("@")[0].capitalize() if "@" in email else "VertiFarm Operator"

        user = db.get_or_create_user({
            "id": user_id,
            "email": email.strip(),
            "name": display_name,
            "role": "Farm Manager",
            "farm_name": "Greenhouse 1",
            "auth_provider": "email",
        })

        token_payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        }
        access_token = create_access_token(token_payload)

        auth_user = AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            farmName=user.farm_name,
            avatarUrl=user.avatar_url,
            authProvider=user.auth_provider,
            googleId=user.google_id,
            accessToken=access_token,
            createdAt=user.created_at,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,
            user=auth_user,
        )

    def signup_with_email(self, name: str, email: str, password: Optional[str] = None) -> TokenResponse:
        """
        Registers a new user profile locally.
        """
        user_id = f"usr-signup-{abs(hash(email)) % 1000000}"
        user = db.get_or_create_user({
            "id": user_id,
            "email": email.strip(),
            "name": name.strip(),
            "role": "Farm Owner",
            "farm_name": "Greenhouse Alpha",
            "auth_provider": "email",
        })

        token_payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        }
        access_token = create_access_token(token_payload)

        auth_user = AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            farmName=user.farm_name,
            avatarUrl=user.avatar_url,
            authProvider=user.auth_provider,
            googleId=user.google_id,
            accessToken=access_token,
            createdAt=user.created_at,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,
            user=auth_user,
        )

auth_service = AuthService()
