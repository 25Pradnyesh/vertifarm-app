from typing import List, Optional
import uuid
import time
from app.db.session import db
from app.models.domain import Sensor as DomainSensor
from app.schemas.sensor import SensorDevice, SensorCreate

class SensorService:
    def get_sensors_for_user(self, user_id: str, farm_id: Optional[str] = None) -> List[SensorDevice]:
        """
        Retrieves all sensors registered to farms accessible to user.
        """
        # User's accessible farm IDs
        user_farm_ids = {f.id for f in db.farms.values() if f.owner_id == user_id or f.owner_id == "usr-default"}
        if farm_id:
            user_farm_ids = user_farm_ids.intersection({farm_id})

        sensors = [s for s in db.sensors.values() if s.farm_id in user_farm_ids]
        
        # If user has their own farm with no sensors yet, provide default sensor set
        if not sensors and farm_id in user_farm_ids:
            return self._provision_default_sensors(farm_id)

        return [
            SensorDevice(
                id=s.id,
                name=s.name,
                type=s.type,
                metric=s.metric,
                zoneId=s.zone_id,
                zoneName=s.zone_name,
                status=s.status, # type: ignore
                lastSeen=s.last_seen,
                batteryLevel=s.battery_level,
            )
            for s in sensors
        ]

    def _provision_default_sensors(self, farm_id: str) -> List[SensorDevice]:
        mock_sensor_data = [
            ("s-temp", "Temperature & Humidity", "DHT22", "temperature"),
            ("s-soil", "Soil Moisture", "Capacitive", "soilMoisture"),
            ("s-ph", "Soil pH", "Analog", "ph"),
            ("s-tds", "TDS Sensor", "Analog", "tds"),
            ("s-light", "Light Sensor", "BH1750", "light"),
            ("s-cam", "Camera (Plant Monitor)", "ESP32-CAM", "camera"),
        ]
        created = []
        for sid_prefix, name, stype, metric in mock_sensor_data:
            sid = f"{sid_prefix}-{farm_id[:6]}"
            sensor = DomainSensor(
                id=sid,
                farm_id=farm_id,
                zone_id=f"z-1-{farm_id[:6]}",
                zone_name="Zone 1",
                name=name,
                type=stype,
                metric=metric,
                status="active",
                last_seen="10:30 AM",
                battery_level=100,
            )
            db.sensors[sid] = sensor
            created.append(SensorDevice(
                id=sensor.id,
                name=sensor.name,
                type=sensor.type,
                metric=sensor.metric,
                zoneId=sensor.zone_id,
                zoneName=sensor.zone_name,
                status=sensor.status, # type: ignore
                lastSeen=sensor.last_seen,
                batteryLevel=sensor.battery_level,
            ))
        return created

    def get_sensor_by_id(self, sensor_id: str, user_id: str) -> Optional[SensorDevice]:
        """
        Retrieves specific sensor device.
        """
        sensor = db.sensors.get(sensor_id)
        if not sensor:
            return None
        return SensorDevice(
            id=sensor.id,
            name=sensor.name,
            type=sensor.type,
            metric=sensor.metric,
            zoneId=sensor.zone_id,
            zoneName=sensor.zone_name,
            status=sensor.status, # type: ignore
            lastSeen=sensor.last_seen,
            batteryLevel=sensor.battery_level,
        )

    def create_sensor(self, user_id: str, data: SensorCreate) -> SensorDevice:
        """
        Registers a new sensor device to a zone and farm.
        """
        sensor_id = f"s-{uuid.uuid4().hex[:6]}"
        farm_id = data.farmId or f"farm-{user_id}"
        new_sensor = DomainSensor(
            id=sensor_id,
            farm_id=farm_id,
            zone_id=data.zoneId,
            zone_name=data.zoneName or "Zone 1",
            name=data.name,
            type=data.type,
            metric=data.metric,
            status=data.status,
            last_seen=time.strftime("%I:%M %p"),
            battery_level=data.batteryLevel or 100,
        )
        db.sensors[sensor_id] = new_sensor

        # Update farm sensor count if present
        if farm_id in db.farms:
            db.farms[farm_id].sensor_count += 1

        return SensorDevice(
            id=new_sensor.id,
            name=new_sensor.name,
            type=new_sensor.type,
            metric=new_sensor.metric,
            zoneId=new_sensor.zone_id,
            zoneName=new_sensor.zone_name,
            status=new_sensor.status, # type: ignore
            lastSeen=new_sensor.last_seen,
            batteryLevel=new_sensor.battery_level,
        )

sensor_service = SensorService()
