from typing import List, Optional
from app.db.session import db
from app.schemas.telemetry import TelemetrySummary, FarmHealthStatus

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

telemetry_service = TelemetryService()
