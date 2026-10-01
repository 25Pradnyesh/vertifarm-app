from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models.domain import User
from app.schemas.farm import Farm, FarmCreate, Zone
from app.services.farm_service import farm_service

router = APIRouter()

@router.get("", response_model=List[Farm])
def list_farms(user: User = Depends(get_current_user)):
    """
    Retrieves all farms owned by the authenticated user.
    """
    return farm_service.get_farms_for_user(user.id)

@router.get("/{farm_id}", response_model=Farm)
def get_farm(farm_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves farm configuration by ID with ownership isolation.
    """
    farm = farm_service.get_farm_by_id(farm_id, user.id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm '{farm_id}' not found.",
        )
    return farm

@router.post("", response_model=Farm, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, user: User = Depends(get_current_user)):
    """
    Provisions a new farm for the authenticated user.
    """
    return farm_service.create_farm(user.id, payload)

@router.get("/{farm_id}/zones", response_model=List[Zone])
def list_zones(farm_id: str, user: User = Depends(get_current_user)):
    """
    Lists cultivation zones in a farm.
    """
    return farm_service.get_zones_for_farm(farm_id, user.id)
