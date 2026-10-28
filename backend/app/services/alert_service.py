import time
import uuid
from typing import List, Optional, Dict
from app.db.session import db
from app.models.domain import Alert, SensorReading
from app.schemas.alert import AlertItem, AlertResolveResponse
from app.core.thresholds import evaluate_reading_threshold
from app.services.realtime_service import realtime_service

class AlertService:
    def __init__(self):
        # In-memory tracking of active violation direction for hysteresis
        # (farm_id, metric) -> direction ("low" | "high")
        self._active_directions: Dict[tuple, str] = {}

    def get_alerts(
        self,
        user_id: str,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = None,
    ) -> List[AlertItem]:
        """
        Retrieves alerts with optional severity and resolution filters.
        """
        user_farm_ids = {f.id for f in db.farms.values() if f.owner_id == user_id or f.owner_id == "usr-default"}
        alerts = [a for a in db.alerts.values() if a.farm_id in user_farm_ids]

        if severity and severity != "all":
            alerts = [a for a in alerts if a.severity == severity]
        if is_resolved is not None:
            alerts = [a for a in alerts if a.is_resolved == is_resolved]

        return [
            AlertItem(
                id=a.id,
                farmId=a.farm_id,
                zoneId=a.zone_id,
                zoneName=a.zone_name,
                metric=a.metric,
                severity=a.severity, # type: ignore
                title=a.title,
                description=a.description,
                currentValue=a.current_value,
                thresholdValue=a.threshold_value,
                timestamp=a.timestamp,
                isResolved=a.is_resolved,
                recommendation=a.recommendation,
            )
            for a in alerts
        ]

    def get_alert_by_id(self, alert_id: str, user_id: str) -> Optional[AlertItem]:
        """
        Retrieves specific alert details.
        """
        a = db.alerts.get(alert_id)
        if not a:
            return None
        return AlertItem(
            id=a.id,
            farmId=a.farm_id,
            zoneId=a.zone_id,
            zoneName=a.zone_name,
            metric=a.metric,
            severity=a.severity, # type: ignore
            title=a.title,
            description=a.description,
            currentValue=a.current_value,
            thresholdValue=a.threshold_value,
            timestamp=a.timestamp,
            isResolved=a.is_resolved,
            recommendation=a.recommendation,
        )

    def resolve_alert(self, alert_id: str, user_id: str) -> Optional[AlertResolveResponse]:
        """
        Marks an alert as resolved.
        """
        alert = db.alerts.get(alert_id)
        if not alert:
            return None
        alert.is_resolved = True
        key = (alert.farm_id, alert.metric)
        self._active_directions.pop(key, None)

        return AlertResolveResponse(
            id=alert.id,
            isResolved=True,
            resolvedAt=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def process_reading_telemetry(self, reading: SensorReading) -> Optional[Alert]:
        """
        Evaluates a newly ingested sensor reading against agronomic thresholds.
        Implements strict deduplication, recovery hysteresis, and real-time alerts.
        """
        farm_id = reading.farm_id or "farm-1"
        metric = reading.metric
        key = (farm_id, metric)

        active_dir = self._active_directions.get(key)
        evaluation = evaluate_reading_threshold(metric, reading.value, active_dir)

        # 1. Reject invalid readings without sending false alerts
        if not evaluation.is_valid:
            return None

        # 2. Check for existing active (unresolved) alert for this metric
        existing_alert = next(
            (
                a for a in db.alerts.values()
                if a.farm_id == farm_id and a.metric == metric and not a.is_resolved
            ),
            None,
        )

        # 3. Violation state
        if evaluation.is_violation:
            if existing_alert:
                # DEDUPLICATION: Reading still exceeds threshold; suppress duplicate alert
                existing_alert.current_value = evaluation.current_value_formatted
                return None

            # NEW VIOLATION: Create alert
            self._active_directions[key] = evaluation.violation_direction or "high"
            time_formatted = time.strftime("%I:%M %p")
            new_alert = Alert(
                id=f"alert-{metric}-{uuid.uuid4().hex[:8]}",
                farm_id=farm_id,
                zone_id=reading.zone_id or "z-1",
                zone_name="Greenhouse 1 - Zone 1",
                metric=metric,
                severity=evaluation.severity,
                title=evaluation.title,
                description=evaluation.notification_body,
                current_value=evaluation.current_value_formatted,
                threshold_value=evaluation.threshold_value_formatted,
                is_resolved=False,
                recommendation=evaluation.recommendation,
                timestamp=time_formatted,
            )

            db.alerts[new_alert.id] = new_alert

            # Broadcast alert creation
            realtime_service.broadcast_sync(
                "alert_created",
                {
                    "id": new_alert.id,
                    "farmId": new_alert.farm_id,
                    "metric": new_alert.metric,
                    "severity": new_alert.severity,
                    "title": new_alert.title,
                    "description": new_alert.description,
                    "currentValue": new_alert.current_value,
                    "thresholdValue": new_alert.threshold_value,
                    "timestamp": new_alert.timestamp,
                    "isResolved": False,
                },
            )

            return new_alert

        # 4. Recovery state
        if existing_alert and not evaluation.is_violation:
            # Value returned to normal range past hysteresis margin
            existing_alert.is_resolved = True
            self._active_directions.pop(key, None)

            # Broadcast alert resolution
            realtime_service.broadcast_sync(
                "alert_resolved",
                {
                    "id": existing_alert.id,
                    "farmId": existing_alert.farm_id,
                    "metric": existing_alert.metric,
                    "isResolved": True,
                },
            )

        return None

alert_service = AlertService()
