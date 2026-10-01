from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.telemetry import TelemetrySummary, FarmHealthStatus
from app.services.telemetry_service import telemetry_service

router = APIRouter()

@router.get("/summary", response_model=List[TelemetrySummary])
def get_telemetry_summaries(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Fetches latest 24-hour summary across all 6 environmental metrics.
    """
    return telemetry_service.get_telemetry_summaries(user.id, farm_id)

@router.get("/health", response_model=FarmHealthStatus)
def get_farm_health(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Evaluates telemetry metrics to report overall farm health.
    """
    return telemetry_service.get_farm_health_status(user.id, farm_id)

@router.get("/{metric}", response_model=TelemetrySummary)
def get_telemetry_by_metric(
    metric: str,
    range: str = Query("24H"),
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Fetches time-series trend points and stats for a specific metric.
    """
    summary = telemetry_service.get_telemetry_by_metric(metric, user.id, farm_id, range)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry metric '{metric}' not found.",
        )
    return summary
