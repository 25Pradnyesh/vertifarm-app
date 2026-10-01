from typing import Optional
from pydantic import BaseModel
from app.schemas.user import AuthUser

class GoogleAuthRequest(BaseModel):
    id_token: str

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

class SignupRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: AuthUser
