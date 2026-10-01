from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.recommendation import RecommendationItem
from app.services.recommendation_service import recommendation_service

router = APIRouter()

@router.get("", response_model=List[RecommendationItem])
def list_recommendations(
    tab: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """
    Retrieves prioritized agronomic guidance and care tips.
    """
    return recommendation_service.get_recommendations(user.id, tab, category)
