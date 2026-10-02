from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

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

class SensorReadingSchema(SchemaBase):
    id: str
    sensor_id: str = Field(..., alias="sensorId")
    metric: str
    value: float
    unit: str
    status: Literal['healthy', 'warning', 'critical', 'offline', 'info'] = 'healthy'
    status_label: Optional[str] = Field(None, alias="statusLabel")
    timestamp: str
    farm_id: Optional[str] = Field(None, alias="farmId")

class TelemetryIngestPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    sensor_id: str = Field(..., alias="sensorId")
    metric: str
    value: float
    unit: Optional[str] = None
    farm_id: Optional[str] = Field(None, alias="farmId")
    zone_id: Optional[str] = Field(None, alias="zoneId")
    timestamp: Optional[str] = None

class TelemetryBatchIngestPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    farm_id: Optional[str] = Field(None, alias="farmId")
    zone_id: Optional[str] = Field(None, alias="zoneId")
    readings: List[TelemetryIngestPayload]

class TelemetryLatestResponse(SchemaBase):
    farm_id: str = Field(..., alias="farmId")
    readings: List[SensorReadingSchema]
    timestamp: str
