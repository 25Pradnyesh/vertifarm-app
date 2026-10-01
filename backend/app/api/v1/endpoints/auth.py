from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import GoogleAuthRequest, LoginRequest, SignupRequest, TokenResponse
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/google", response_model=TokenResponse)
def authenticate_google(payload: GoogleAuthRequest):
    """
    Verifies a Google ID token from mobile client and issues an authenticated session token.
    """
    try:
        return auth_service.authenticate_google_token(payload.id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}",
        )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Authenticates operator with email and password.
    """
    try:
        return auth_service.login_with_email(payload.email, payload.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}",
        )

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    """
    Registers a new grower account.
    """
    try:
        return auth_service.signup_with_email(payload.name, payload.email, payload.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}",
        )

@router.post("/logout")
def logout():
    """
    Invalidates current session on the backend.
    """
    return {"success": True}
