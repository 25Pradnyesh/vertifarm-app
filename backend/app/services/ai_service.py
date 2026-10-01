from typing import List, Optional
from app.db.session import db
from app.schemas.scan import AIScan, CameraCapture

class AIService:
    def get_scans(self, user_id: str) -> List[AIScan]:
        """
        Retrieves historical AI plant health diagnosis scans.
        """
        scans = [s for s in db.scans.values() if s.user_id == user_id or s.user_id == "usr-default"]
        return [
            AIScan(
                id=s.id,
                plantType=s.plant_type,
                diseaseName=s.disease_name,
                isHealthy=s.is_healthy,
                confidence=s.confidence,
                imageUrl=s.image_url,
                timestamp=s.timestamp,
                recommendations=s.recommendations,
            )
            for s in scans
        ]

    def get_scan_by_id(self, scan_id: str, user_id: str) -> Optional[AIScan]:
        """
        Retrieves specific scan details.
        """
        s = db.scans.get(scan_id)
        if not s:
            return None
        return AIScan(
            id=s.id,
            plantType=s.plant_type,
            diseaseName=s.disease_name,
            isHealthy=s.is_healthy,
            confidence=s.confidence,
            imageUrl=s.image_url,
            timestamp=s.timestamp,
            recommendations=s.recommendations,
        )

    def get_camera_status(self, user_id: str) -> CameraCapture:
        """
        Retrieves optical camera status.
        """
        cam = next(iter(db.camera_captures.values()), None)
        if cam:
            return CameraCapture(
                id=cam.id,
                cameraId=cam.camera_id,
                zoneName=cam.zone_name,
                imageUrl=cam.image_url,
                timestamp=cam.timestamp,
                isLive=cam.is_live,
                nextCaptureIn=cam.next_capture_in,
            )
        return CameraCapture(
            id="cam-1",
            cameraId="ESP32-CAM-01",
            zoneName="Greenhouse 1 - Zone 1",
            imageUrl="https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800",
            timestamp="10:30 AM",
            isLive=True,
            nextCaptureIn="04:52",
        )

ai_service = AIService()
