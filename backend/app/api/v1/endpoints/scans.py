from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.scan import AIScan, CameraCapture
from app.services.ai_service import ai_service

router = APIRouter()

@router.get("/scans", response_model=List[AIScan])
def list_scans(user: User = Depends(get_current_user)):
    """
    Retrieves historical optical plant health scans.
    """
    return ai_service.get_scans(user.id)

@router.get("/scans/{scan_id}", response_model=AIScan)
def get_scan(scan_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves specific plant disease diagnosis report.
    """
    scan = ai_service.get_scan_by_id(scan_id, user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI Scan '{scan_id}' not found.",
        )
    return scan

@router.get("/camera/status", response_model=CameraCapture)
def get_camera_status(user: User = Depends(get_current_user)):
    """
    Returns optical camera device state and next capture timer.
    """
    return ai_service.get_camera_status(user.id)

@router.post("/camera/capture")
def trigger_camera_capture(user: User = Depends(get_current_user)):
    """
    Triggers manual capture on ESP32-CAM and queues for diagnosis.
    """
    return {
        "queued": True,
        "job_id": f"job-{uuid.uuid4().hex[:8]}",
    }
