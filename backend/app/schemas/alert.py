from typing import Literal
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class AlertItem(SchemaBase):
    id: str
    farmId: str
    zoneId: str
    zoneName: str
    metric: str
    severity: Literal['critical', 'warning', 'info']
    title: str
    description: str
    currentValue: str
    thresholdValue: str
    timestamp: str
    isResolved: bool = False
    recommendation: str

class AlertResolveResponse(SchemaBase):
    id: str
    isResolved: bool
    resolvedAt: str
