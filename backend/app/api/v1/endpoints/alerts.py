from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.alert import (
    AlertItem,
    AlertResolveResponse,
    ThresholdEvaluationRequest,
    ThresholdEvaluationResponse,
)
from app.services.alert_service import alert_service
from app.core.thresholds import evaluate_reading_threshold

router = APIRouter()

@router.get("", response_model=List[AlertItem])
def list_alerts(
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None, alias="isResolved"),
    user: User = Depends(get_current_user),
):
    """
    Retrieves operational notifications with optional severity/resolution filters.
    """
    return alert_service.get_alerts(user.id, severity, is_resolved)

@router.post("/evaluate", response_model=ThresholdEvaluationResponse)
def evaluate_metric_threshold(
    payload: ThresholdEvaluationRequest,
):
    """
    Evaluates sensor reading against centralized agronomic thresholds.
    """
    res = evaluate_reading_threshold(payload.metric, payload.value, payload.activeViolationDirection)
    return ThresholdEvaluationResponse(
        isValid=res.is_valid,
        status=res.status,
        severity=res.severity,
        statusLabel=res.status_label,
        isViolation=res.is_violation,
        violationDirection=res.violation_direction,
        title=res.title,
        notificationBody=res.notification_body,
        currentValueFormatted=res.current_value_formatted,
        thresholdValueFormatted=res.threshold_value_formatted,
        recommendation=res.recommendation,
    )

@router.get("/{alert_id}", response_model=AlertItem)
def get_alert(alert_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves full diagnostic detail and recommendation for a specific alert.
    """
    alert = alert_service.get_alert_by_id(alert_id, user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return alert

@router.post("/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert(alert_id: str, user: User = Depends(get_current_user)):
    """
    Marks an operational alert as resolved by the operator.
    """
    res = alert_service.resolve_alert(alert_id, user.id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return res
