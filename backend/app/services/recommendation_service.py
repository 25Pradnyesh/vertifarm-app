from typing import List, Optional
from app.db.session import db
from app.schemas.recommendation import RecommendationItem

class RecommendationService:
    def get_recommendations(
        self, user_id: str, tab: Optional[str] = None, category: Optional[str] = None
    ) -> List[RecommendationItem]:
        """
        Retrieves agronomic recommendations filtered by tab or category.
        """
        recs = [r for r in db.recommendations.values() if r.user_id is None or r.user_id == user_id or r.user_id == "usr-default"]
        if tab:
            recs = [r for r in recs if r.tab == tab]
        if category:
            recs = [r for r in recs if r.category == category]

        return [
            RecommendationItem(
                id=r.id,
                category=r.category, # type: ignore
                title=r.title,
                description=r.description,
                priority=r.priority, # type: ignore
                tab=r.tab, # type: ignore
                actionableLink=r.actionable_link,
            )
            for r in recs
        ]

recommendation_service = RecommendationService()
