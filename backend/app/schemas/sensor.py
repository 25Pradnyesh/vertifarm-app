from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class SensorDevice(SchemaBase):
    id: str
    name: str
    type: str
    metric: str
    zoneId: str
    zoneName: str
    status: Literal['active', 'warning', 'offline'] = 'active'
    lastSeen: str
    batteryLevel: Optional[int] = None

class SensorCreate(SchemaBase):
    name: str
    type: str
    metric: str
    zoneId: str
    farmId: Optional[str] = None
    zoneName: Optional[str] = "Zone 1"
    status: Literal['active', 'warning', 'offline'] = 'active'
    batteryLevel: Optional[int] = 100
