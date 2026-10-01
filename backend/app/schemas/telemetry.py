from typing import List, Literal
from pydantic import BaseModel, ConfigDict

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class TelemetrySummary(SchemaBase):
    metric: str
    name: str
    currentValue: float
    unit: str
    status: Literal['healthy', 'warning', 'critical', 'offline', 'info'] = 'healthy'
    statusLabel: str
    min: float
    max: float
    avg: float
    optimalMin: float
    optimalMax: float
    optimalText: str
    trend: List[float] = []
    timestamps: List[str] = []

class FarmHealthStatus(SchemaBase):
    status: Literal['healthy', 'warning', 'critical'] = 'healthy'
    message: str
