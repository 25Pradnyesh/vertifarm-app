from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.sensor import SensorDevice, SensorCreate
from app.services.sensor_service import sensor_service

router = APIRouter()

@router.get("", response_model=List[SensorDevice])
def list_sensors(
    farm_id: Optional[str] = Query(None, alias="farmId"),
    user: User = Depends(get_current_user),
):
    """
    Returns inventory of hardware sensor devices across user's farms.
    """
    return sensor_service.get_sensors_for_user(user.id, farm_id)

@router.get("/{sensor_id}", response_model=SensorDevice)
def get_sensor(sensor_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves health, metric, and status for a specific sensor device.
    """
    sensor = sensor_service.get_sensor_by_id(sensor_id, user.id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor device '{sensor_id}' not found.",
        )
    return sensor

@router.post("", response_model=SensorDevice, status_code=status.HTTP_201_CREATED)
def create_sensor(payload: SensorCreate, user: User = Depends(get_current_user)):
    """
    Pairs and registers a new sensor device.
    """
    return sensor_service.create_sensor(user.id, payload)
