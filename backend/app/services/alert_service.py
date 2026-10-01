from typing import List, Optional
import time
from app.db.session import db
from app.schemas.alert import AlertItem, AlertResolveResponse

class AlertService:
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
        return AlertResolveResponse(
            id=alert.id,
            isResolved=True,
            resolvedAt=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

alert_service = AlertService()
