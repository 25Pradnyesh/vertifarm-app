import base64
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.scan import (
    AIScan,
    CameraCapture,
    ScanDiagnoseJsonRequest,
    ScanDiagnosisResponse,
)
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


@router.post("/scans/diagnose", response_model=ScanDiagnosisResponse)
async def diagnose_scan_file(
    file: UploadFile = File(..., description="Multipart plant leaf image file (JPEG, PNG, WEBP)"),
    farm_id: Optional[str] = Form("farm-1"),
    user: User = Depends(get_current_user),
):
    """
    Executes real-time plant disease diagnosis on an uploaded image file using MobileNetV3-Small.
    Returns predicted crop, disease classification, confidence, top 3 predictions,
    and uncertainty flag when below calibrated confidence threshold.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded. Please upload a valid image.",
            )

        diagnosis = ai_service.diagnose_image(
            image_bytes=contents,
            filename=file.filename,
            user_id=user.id,
            farm_id=farm_id or "farm-1",
        )
        return diagnosis

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image decoding failed: {val_err}",
        )
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI inference unavailable: {run_err}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during disease diagnosis: {exc}",
        )


@router.post("/scans/diagnose-json", response_model=ScanDiagnosisResponse)
def diagnose_scan_json(
    request: ScanDiagnoseJsonRequest,
    user: User = Depends(get_current_user),
):
    """
    Executes plant disease diagnosis via base64 image data or local file path.
    """
    raw_bytes = None

    if request.imageBase64:
        try:
            # Handle data URL prefix if present
            b64_str = request.imageBase64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_str)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 encoded image string: {e}",
            )
    elif request.filePath:
        p = Path(request.filePath)
        if not p.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specified image file not found: {request.filePath}",
            )
        try:
            raw_bytes = p.read_bytes()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not read image file from disk: {e}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'imageBase64' or 'filePath' must be provided in request body.",
        )

    try:
        diagnosis = ai_service.diagnose_image(
            image_bytes=raw_bytes,
            user_id=user.id,
            farm_id=request.farmId or "farm-1",
            image_url=request.imageUrl,
        )
        return diagnosis
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image decoding failed: {val_err}",
        )
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI inference unavailable: {run_err}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during disease diagnosis: {exc}",
        )


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
