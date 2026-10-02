from dataclasses import dataclass, field
from typing import Optional, List
import time

@dataclass
class User:
    id: str
    email: str
    name: str
    role: str = "Farm Owner"
    farm_name: str = "Greenhouse 1"
    avatar_url: Optional[str] = None
    auth_provider: str = "google"
    google_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

@dataclass
class Farm:
    id: str
    owner_id: str
    name: str
    location: str
    sensor_count: int = 0
    zone_count: int = 0
    is_active: bool = True
    image_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

@dataclass
class Zone:
    id: str
    farm_id: str
    name: str
    crop: str
    sensor_count: int = 0

@dataclass
class Sensor:
    id: str
    farm_id: str
    zone_id: str
    zone_name: str
    name: str
    type: str
    metric: str
    status: str = "active"
    last_seen: str = "Just now"
    battery_level: Optional[int] = 100

@dataclass
class SensorReading:
    id: str
    sensor_id: str
    farm_id: str
    metric: str
    value: float
    unit: str
    status: str = "healthy"
    status_label: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    zone_id: Optional[str] = None

@dataclass
class TelemetryPoint:

    metric: str
    name: str
    current_value: float
    unit: str
    status: str
    status_label: str
    min_val: float
    max_val: float
    avg_val: float
    optimal_min: float
    optimal_max: float
    optimal_text: str
    trend: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)

@dataclass
class Alert:
    id: str
    farm_id: str
    zone_id: str
    zone_name: str
    metric: str
    severity: str
    title: str
    description: str
    current_value: str
    threshold_value: str
    is_resolved: bool = False
    recommendation: str = ""
    timestamp: str = "Just now"

@dataclass
class AIScan:
    id: str
    farm_id: str
    user_id: str
    plant_type: str
    disease_name: str
    is_healthy: bool
    confidence: float
    image_url: str
    timestamp: str
    recommendations: List[str] = field(default_factory=list)

@dataclass
class CameraCapture:
    id: str
    camera_id: str
    farm_id: str
    zone_name: str
    image_url: str
    timestamp: str
    is_live: bool = True
    next_capture_in: str = "04:52"

@dataclass
class Recommendation:
    id: str
    farm_id: str
    user_id: Optional[str]
    category: str
    title: str
    description: str
    priority: str
    tab: str
    actionable_link: Optional[str] = None
