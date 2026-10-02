from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class PredictionDetail(SchemaBase):
    class_name: str
    crop: str
    disease: str
    is_healthy: bool
    confidence: float


class AIScan(SchemaBase):
    id: str
    plantType: str
    diseaseName: str
    isHealthy: bool
    confidence: float
    imageUrl: str
    timestamp: str
    recommendations: List[str] = []


class ScanDiagnosisResponse(AIScan):
    predictedCrop: str
    predictedDisease: str
    rawClass: str
    isUncertain: bool = False
    uncertaintyMessage: Optional[str] = None
    topPredictions: List[PredictionDetail] = []
    thresholdApplied: float = 0.60


class ScanDiagnoseJsonRequest(SchemaBase):
    imageBase64: Optional[str] = None
    filePath: Optional[str] = None
    imageUrl: Optional[str] = None
    farmId: Optional[str] = "farm-1"


class CameraCapture(SchemaBase):
    id: str
    cameraId: str
    zoneName: str
    imageUrl: str
    timestamp: str
    isLive: bool = True
    nextCaptureIn: str = "04:52"
