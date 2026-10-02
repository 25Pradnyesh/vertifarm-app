from typing import List, Optional
import time
from app.db.session import db
from app.schemas.telemetry import (
    TelemetrySummary,
    FarmHealthStatus,
    SensorReadingSchema,
    TelemetryIngestPayload,
)

class TelemetryService:
    def get_telemetry_summaries(self, user_id: str, farm_id: Optional[str] = None) -> List[TelemetrySummary]:
        """
        Retrieves 24-hour telemetry summaries across all 6 environmental metrics.
        """
        target_farm = farm_id or "farm-1"
        summaries_map = db.telemetry_summaries.get(target_farm) or db.telemetry_summaries.get("farm-1", {})

        return [
            TelemetrySummary(
                metric=p.metric,
                name=p.name,
                currentValue=p.current_value,
                unit=p.unit,
                status=p.status, # type: ignore
                statusLabel=p.status_label,
                min=p.min_val,
                max=p.max_val,
                avg=p.avg_val,
                optimalMin=p.optimal_min,
                optimalMax=p.optimal_max,
                optimalText=p.optimal_text,
                trend=p.trend,
                timestamps=p.timestamps,
            )
            for p in summaries_map.values()
        ]

    def get_telemetry_by_metric(
        self, metric: str, user_id: str, farm_id: Optional[str] = None, range_str: str = "24H"
    ) -> Optional[TelemetrySummary]:
        """
        Retrieves telemetry summary for a single metric.
        """
        target_farm = farm_id or "farm-1"
        summaries_map = db.telemetry_summaries.get(target_farm) or db.telemetry_summaries.get("farm-1", {})
        p = summaries_map.get(metric)
        if not p:
            return None

        return TelemetrySummary(
            metric=p.metric,
            name=p.name,
            currentValue=p.current_value,
            unit=p.unit,
            status=p.status, # type: ignore
            statusLabel=p.status_label,
            min=p.min_val,
            max=p.max_val,
            avg=p.avg_val,
            optimalMin=p.optimal_min,
            optimalMax=p.optimal_max,
            optimalText=p.optimal_text,
            trend=p.trend,
            timestamps=p.timestamps,
        )

    def get_farm_health_status(self, user_id: str, farm_id: Optional[str] = None) -> FarmHealthStatus:
        """
        Evaluates overall farm health based on current telemetry statuses.
        """
        summaries = self.get_telemetry_summaries(user_id, farm_id)
        critical_count = sum(1 for s in summaries if s.status == "critical")
        warning_count = sum(1 for s in summaries if s.status == "warning")

        if critical_count > 0:
            return FarmHealthStatus(
                status="critical",
                message="Some parameters require immediate attention.",
            )
        if warning_count > 0:
            return FarmHealthStatus(
                status="warning",
                message="Some parameters need monitoring.",
            )
        return FarmHealthStatus(
            status="healthy",
            message="All systems are running smoothly.",
        )

    def get_latest_readings(self, user_id: str, farm_id: Optional[str] = None) -> List[SensorReadingSchema]:
        """
        Retrieves latest real-time sensor readings snapshot across metrics for a farm.
        """
        target_farm = farm_id or "farm-1"
        raw_readings = db.get_latest_readings(target_farm)
        return [
            SensorReadingSchema(
                id=r.id,
                sensor_id=r.sensor_id,
                farm_id=r.farm_id,
                metric=r.metric,
                value=r.value,
                unit=r.unit,
                status=r.status, # type: ignore
                status_label=r.status_label,
                timestamp=r.timestamp,
            )
            for r in raw_readings
        ]

    def get_readings_history(
        self,
        user_id: str,
        farm_id: Optional[str] = None,
        metric: Optional[str] = None,
        limit: int = 50,
    ) -> List[SensorReadingSchema]:
        """
        Retrieves time-series history log of sensor readings.
        """
        target_farm = farm_id or "farm-1"
        raw_readings = db.get_sensor_readings(farm_id=target_farm, metric=metric, limit=limit)
        return [
            SensorReadingSchema(
                id=r.id,
                sensor_id=r.sensor_id,
                farm_id=r.farm_id,
                metric=r.metric,
                value=r.value,
                unit=r.unit,
                status=r.status, # type: ignore
                status_label=r.status_label,
                timestamp=r.timestamp,
            )
            for r in raw_readings
        ]

    def ingest_reading(self, payload: TelemetryIngestPayload) -> Optional[SensorReadingSchema]:
        """
        Ingests reading through the unified MQTT/HTTP validation and persistence pipeline.
        """
        from app.services.mqtt_service import mqtt_service

        recorded = mqtt_service.ingest_reading(
            sensor_id=payload.sensor_id,
            metric=payload.metric,
            value=payload.value,
            unit=payload.unit,
            farm_id=payload.farm_id,
            zone_id=payload.zone_id,
            timestamp=payload.timestamp,
        )
        if not recorded:
            return None

        return SensorReadingSchema(
            id=recorded.id,
            sensor_id=recorded.sensor_id,
            farm_id=recorded.farm_id,
            metric=recorded.metric,
            value=recorded.value,
            unit=recorded.unit,
            status=recorded.status, # type: ignore
            status_label=recorded.status_label,
            timestamp=recorded.timestamp,
        )

telemetry_service = TelemetryService()
