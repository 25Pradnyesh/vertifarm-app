from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    farms,
    sensors,
    telemetry,
    alerts,
    scans,
    recommendations,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(scans.router, prefix="/ai", tags=["AI & Plant Health"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
