from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.user import AuthUser, UserUpdate

router = APIRouter()

@router.get("/me", response_model=AuthUser)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and active farm affiliation.
    """
    return AuthUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        farmName=user.farm_name,
        avatarUrl=user.avatar_url,
        authProvider=user.auth_provider,
        googleId=user.google_id,
        createdAt=user.created_at,
    )

@router.patch("/me", response_model=AuthUser)
def update_current_user_profile(update_data: UserUpdate, user: User = Depends(get_current_user)):
    """
    Updates operator preferences or display name.
    """
    if update_data.name:
        user.name = update_data.name
    if update_data.role:
        user.role = update_data.role
    if update_data.farmName:
        user.farm_name = update_data.farmName
    if update_data.avatarUrl:
        user.avatar_url = update_data.avatarUrl

    return AuthUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        farmName=user.farm_name,
        avatarUrl=user.avatar_url,
        authProvider=user.auth_provider,
        googleId=user.google_id,
        createdAt=user.created_at,
    )
