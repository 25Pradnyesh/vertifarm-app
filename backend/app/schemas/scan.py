from typing import List
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class AIScan(SchemaBase):
    id: str
    plantType: str
    diseaseName: str
    isHealthy: bool
    confidence: float
    imageUrl: str
    timestamp: str
    recommendations: List[str] = []

class CameraCapture(SchemaBase):
    id: str
    cameraId: str
    zoneName: str
    imageUrl: str
    timestamp: str
    isLive: bool = True
    nextCaptureIn: str = "04:52"
