from typing import Dict, List, Optional
import time
import uuid
from app.models.domain import (
    User,
    Farm,
    Zone,
    Sensor,
    TelemetryPoint,
    Alert,
    AIScan,
    CameraCapture,
    Recommendation,
)

class InMemoryDatabase:
    """
    Database repository implementing the PostgreSQL/Supabase schema for Stage 4.
    Enforces user isolation, foreign key relationships, and seed hydration.
    """
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.farms: Dict[str, Farm] = {}
        self.zones: Dict[str, Zone] = {}
        self.sensors: Dict[str, Sensor] = {}
        self.alerts: Dict[str, Alert] = {}
        self.scans: Dict[str, AIScan] = {}
        self.camera_captures: Dict[str, CameraCapture] = {}
        self.recommendations: Dict[str, Recommendation] = {}
        self.telemetry_summaries: Dict[str, Dict[str, TelemetryPoint]] = {} # farm_id -> metric -> TelemetryPoint
        
        self._seed_default_data()

    def _seed_default_data(self):
        # Default seed user
        default_user_id = "usr-default"
        self.users[default_user_id] = User(
            id=default_user_id,
            email="grower@vertifarm.io",
            name="VertiFarm Grower",
            role="Farm Owner",
            farm_name="Greenhouse 1",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200",
            auth_provider="google",
            google_id="google-sub-default",
        )

        # Seed farms
        farm1_id = "farm-1"
        self.farms[farm1_id] = Farm(
            id=farm1_id,
            owner_id=default_user_id,
            name="Greenhouse 1",
            location="Pune, Maharashtra, India",
            sensor_count=12,
            zone_count=2,
            is_active=True,
            image_url="https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600",
            created_at="2025-01-15",
        )

        farm2_id = "farm-2"
        self.farms[farm2_id] = Farm(
            id=farm2_id,
            owner_id=default_user_id,
            name="Greenhouse 2",
            location="Nashik, Maharashtra, India",
            sensor_count=8,
            zone_count=1,
            is_active=False,
            image_url="https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600",
            created_at="2025-02-20",
        )

        # Seed zones
        zone1_id = "z-1"
        self.zones[zone1_id] = Zone(
            id=zone1_id,
            farm_id=farm1_id,
            name="Zone 1",
            crop="Tomato",
            sensor_count=6,
        )

        # Seed sensors
        mock_sensor_data = [
            ("s-1", "Temperature & Humidity", "DHT22", "temperature"),
            ("s-2", "Soil Moisture", "Capacitive", "soilMoisture"),
            ("s-3", "Soil pH", "Analog", "ph"),
            ("s-4", "TDS Sensor", "Analog", "tds"),
            ("s-5", "Light Sensor", "BH1750", "light"),
            ("s-6", "Camera (Plant Monitor)", "ESP32-CAM", "camera"),
        ]
        for sid, name, stype, metric in mock_sensor_data:
            self.sensors[sid] = Sensor(
                id=sid,
                farm_id=farm1_id,
                zone_id=zone1_id,
                zone_name="Zone 1",
                name=name,
                type=stype,
                metric=metric,
                status="active",
                last_seen="10:30 AM",
                battery_level=100,
            )

        # Seed telemetry
        self.telemetry_summaries[farm1_id] = {
            "temperature": TelemetryPoint(
                metric="temperature",
                name="Temperature",
                current_value=32.6,
                unit="°C",
                status="healthy",
                status_label="Normal",
                min_val=24.1,
                max_val=33.8,
                avg_val=32.6,
                optimal_min=20.0,
                optimal_max=30.0,
                optimal_text="For healthy growth",
                trend=[28.2, 29.5, 31.0, 32.6],
                timestamps=["07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM"],
            ),
            "humidity": TelemetryPoint(
                metric="humidity",
                name="Humidity",
                current_value=65.4,
                unit="%",
                status="healthy",
                status_label="Normal",
                min_val=58.2,
                max_val=72.1,
                avg_val=65.4,
                optimal_min=60.0,
                optimal_max=80.0,
                optimal_text="For healthy growth",
                trend=[62.0, 64.1, 65.4],
                timestamps=["08:00 AM", "09:00 AM", "10:00 AM"],
            ),
            "soilMoisture": TelemetryPoint(
                metric="soilMoisture",
                name="Soil Moisture",
                current_value=48.0,
                unit="%",
                status="healthy",
                status_label="Normal",
                min_val=42.0,
                max_val=54.0,
                avg_val=48.0,
                optimal_min=40.0,
                optimal_max=60.0,
                optimal_text="For healthy growth",
                trend=[50.0, 49.0, 48.0],
                timestamps=["08:00 AM", "09:00 AM", "10:00 AM"],
            ),
            "ph": TelemetryPoint(
                metric="ph",
                name="Soil pH",
                current_value=6.58,
                unit="pH",
                status="healthy",
                status_label="Slightly Acidic",
                min_val=6.2,
                max_val=6.9,
                avg_val=6.58,
                optimal_min=6.0,
                optimal_max=7.0,
                optimal_text="For healthy growth",
                trend=[6.6, 6.55, 6.58],
                timestamps=["08:00 AM", "09:00 AM", "10:00 AM"],
            ),
            "tds": TelemetryPoint(
                metric="tds",
                name="TDS",
                current_value=620.0,
                unit="ppm",
                status="healthy",
                status_label="Normal",
                min_val=580.0,
                max_val=670.0,
                avg_val=620.0,
                optimal_min=500.0,
                optimal_max=800.0,
                optimal_text="For healthy growth",
                trend=[610.0, 615.0, 620.0],
                timestamps=["08:00 AM", "09:00 AM", "10:00 AM"],
            ),
            "light": TelemetryPoint(
                metric="light",
                name="Light Intensity",
                current_value=1200.0,
                unit="Lux",
                status="healthy",
                status_label="Optimal",
                min_val=800.0,
                max_val=1500.0,
                avg_val=1200.0,
                optimal_min=1000.0,
                optimal_max=2000.0,
                optimal_text="Optimal light for photosynthesis",
                trend=[950.0, 1100.0, 1200.0],
                timestamps=["08:00 AM", "09:00 AM", "10:00 AM"],
            ),
        }

        # Seed alerts
        self.alerts["alert-1"] = Alert(
            id="alert-1",
            farm_id=farm1_id,
            zone_id=zone1_id,
            zone_name="Greenhouse 1 - Zone 1",
            metric="soilMoisture",
            severity="critical",
            title="Soil Moisture is Low",
            description="Irrigation recommended",
            current_value="28%",
            threshold_value="< 30%",
            timestamp="10:28 AM",
            is_resolved=False,
            recommendation="Irrigation is recommended to maintain optimal soil moisture for healthy plant growth.",
        )
        self.alerts["alert-2"] = Alert(
            id="alert-2",
            farm_id=farm1_id,
            zone_id=zone1_id,
            zone_name="Greenhouse 1 - Zone 1",
            metric="ph",
            severity="warning",
            title="pH Level is Slightly High",
            description="Consider adjusting nutrient...",
            current_value="7.2 pH",
            threshold_value="> 7.0 pH",
            timestamp="10:15 AM",
            is_resolved=False,
            recommendation="pH is slightly high. Add organic matter or pH down solution to lower the pH level.",
        )
        self.alerts["alert-3"] = Alert(
            id="alert-3",
            farm_id=farm1_id,
            zone_id=zone1_id,
            zone_name="Greenhouse 1 - Zone 1",
            metric="temperature",
            severity="warning",
            title="Temperature is High",
            description="Check ventilation or cooling...",
            current_value="34°C",
            threshold_value="> 32°C",
            timestamp="09:50 AM",
            is_resolved=False,
            recommendation="Temperature is elevated. Check ventilation systems, increase airflow, or activate cooling equipment.",
        )

        # Seed scans
        self.scans["scan-1"] = AIScan(
            id="scan-1",
            farm_id=farm1_id,
            user_id=default_user_id,
            plant_type="Tomato Plant",
            disease_name="Leaf Spot",
            is_healthy=False,
            confidence=92.6,
            image_url="https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600",
            timestamp="Today, 10:28 AM",
            recommendations=[
                "Remove affected leaves immediately",
                "Improve air circulation around canopy",
                "Apply suitable organic fungicide",
                "Monitor humidity levels closely",
            ],
        )

        # Seed camera
        self.camera_captures["cam-1"] = CameraCapture(
            id="cam-1",
            camera_id="ESP32-CAM-01",
            farm_id=farm1_id,
            zone_name="Greenhouse 1 - Zone 1",
            image_url="https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800",
            timestamp="10:30 AM",
            is_live=True,
            next_capture_in="04:52",
        )

        # Seed recommendations
        self.recommendations["rec-1"] = Recommendation(
            id="rec-1",
            farm_id=farm1_id,
            user_id=default_user_id,
            category="irrigation",
            title="Irrigation Recommendation",
            description="Soil moisture is below optimal range. Consider irrigation.",
            priority="high",
            tab="forYou",
            actionable_link="/live-data/soilMoisture",
        )
        self.recommendations["rec-2"] = Recommendation(
            id="rec-2",
            farm_id=farm1_id,
            user_id=default_user_id,
            category="ph",
            title="pH Adjustment",
            description="pH is slightly high. Add organic matter or pH down solution.",
            priority="medium",
            tab="forYou",
            actionable_link="/live-data/ph",
        )
        self.recommendations["rec-3"] = Recommendation(
            id="rec-3",
            farm_id=farm1_id,
            user_id=None,
            category="nutrition",
            title="Nutrition Management",
            description="TDS is in good range. Maintain current nutrient concentration.",
            priority="low",
            tab="general",
            actionable_link="/live-data/tds",
        )

    def get_or_create_user(self, user_data: dict) -> User:
        user_id = user_data["id"]
        if user_id in self.users:
            user = self.users[user_id]
            # Update fields if provided
            if "name" in user_data and user_data["name"]:
                user.name = user_data["name"]
            if "picture" in user_data and user_data["picture"]:
                user.avatar_url = user_data["picture"]
            return user

        # Create new user
        new_user = User(
            id=user_id,
            email=user_data.get("email", f"{user_id}@vertifarm.io"),
            name=user_data.get("name", "VertiFarm Grower"),
            role=user_data.get("role", "Farm Owner"),
            farm_name=user_data.get("farm_name", "My Greenhouse"),
            avatar_url=user_data.get("picture"),
            auth_provider=user_data.get("auth_provider", "google"),
            google_id=user_data.get("google_id"),
        )
        self.users[user_id] = new_user

        # Automatically provision initial personal farm for new user
        farm_id = f"farm-{user_id}"
        self.farms[farm_id] = Farm(
            id=farm_id,
            owner_id=user_id,
            name=new_user.farm_name,
            location="Indoor Facility",
            sensor_count=6,
            zone_count=1,
            is_active=True,
            image_url="https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600",
            created_at=time.strftime("%Y-%m-%d"),
        )
        zone_id = f"zone-{user_id}"
        self.zones[zone_id] = Zone(
            id=zone_id,
            farm_id=farm_id,
            name="Zone 1",
            crop="Tomato",
            sensor_count=6,
        )

        return new_user

# Global database singleton
db = InMemoryDatabase()
