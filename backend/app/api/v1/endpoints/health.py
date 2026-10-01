import time
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str

@router.get("", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
