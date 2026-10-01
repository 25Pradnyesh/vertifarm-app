from typing import Optional
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class Zone(SchemaBase):
    id: str
    farmId: str
    name: str
    crop: str
    sensorCount: int = 0

class Farm(SchemaBase):
    id: str
    name: str
    location: str
    sensorCount: int = 0
    zoneCount: int = 0
    isActive: bool = True
    imageUrl: Optional[str] = None
    createdAt: str

class FarmCreate(SchemaBase):
    name: str
    location: str
    imageUrl: Optional[str] = None
    isActive: bool = True

class FarmUpdate(SchemaBase):
    name: Optional[str] = None
    location: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
