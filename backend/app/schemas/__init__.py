from app.schemas.user import UserProfile, AuthUser, UserUpdate
from app.schemas.auth import GoogleAuthRequest, LoginRequest, SignupRequest, TokenResponse
from app.schemas.farm import Farm, FarmCreate, FarmUpdate, Zone
from app.schemas.sensor import SensorDevice, SensorCreate
from app.schemas.telemetry import TelemetrySummary, FarmHealthStatus
from app.schemas.alert import AlertItem, AlertResolveResponse
from app.schemas.scan import AIScan, CameraCapture
from app.schemas.recommendation import RecommendationItem

__all__ = [
    "UserProfile",
    "AuthUser",
    "UserUpdate",
    "GoogleAuthRequest",
    "LoginRequest",
    "SignupRequest",
    "TokenResponse",
    "Farm",
    "FarmCreate",
    "FarmUpdate",
    "Zone",
    "SensorDevice",
    "SensorCreate",
    "TelemetrySummary",
    "FarmHealthStatus",
    "AlertItem",
    "AlertResolveResponse",
    "AIScan",
    "CameraCapture",
    "RecommendationItem",
]
