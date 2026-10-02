import io
import json
import logging
import os
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple
import uuid

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from app.core.config import settings
from app.db.session import db
from app.models.domain import AIScan as DomainAIScan
from app.schemas.scan import (
    AIScan,
    CameraCapture,
    PredictionDetail,
    ScanDiagnosisResponse,
)

logger = logging.getLogger(__name__)

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

CROP_MAPPING = {
    "coriander_bacterial_blight": {
        "crop": "Coriander",
        "disease": "Bacterial Blight",
        "is_healthy": False,
        "recommendations": [
            "Prune and dispose of severely infected leaves to prevent bacterial spread.",
            "Reduce canopy humidity by improving ventilation and plant spacing.",
            "Avoid overhead irrigation; transition to drip or targeted root watering.",
            "Apply copper-based bactericide or approved biological control spray.",
        ],
    },
    "coriander_healthy": {
        "crop": "Coriander",
        "disease": "Healthy",
        "is_healthy": True,
        "recommendations": [
            "Foliage demonstrates strong chlorophyll density and healthy leaf morphology.",
            "Maintain current EC, pH, and photoperiod targets for the vegetative growth phase.",
            "Continue automated microclimate regulation and preventive scouting.",
        ],
    },
    "coriander_powdery_mildew": {
        "crop": "Coriander",
        "disease": "Powdery Mildew",
        "is_healthy": False,
        "recommendations": [
            "Isolate affected trays to prevent airborne conidiospore dissemination.",
            "Maintain relative humidity below 65% in the canopy layer.",
            "Apply potassium bicarbonate spray or neem-based organic bio-fungicide.",
            "Increase air circulation using oscillating airflow fans.",
        ],
    },
    "fenugreek_bacterial_blight": {
        "crop": "Fenugreek",
        "disease": "Bacterial Blight",
        "is_healthy": False,
        "recommendations": [
            "Excise symptomatic foliage with sterilized pruning instruments.",
            "Ensure foliage dries rapidly following any localized humidity spikes.",
            "Adjust nighttime temperatures to avoid condensation on leaf surfaces.",
            "Apply agricultural copper sulfate or bio-bactericide if lesions progress.",
        ],
    },
    "fenugreek_cercospora_leaf_spot": {
        "crop": "Fenugreek",
        "disease": "Cercospora Leaf Spot",
        "is_healthy": False,
        "recommendations": [
            "Remove lower foliage displaying dark circular necrotic leaf spots.",
            "Improve vertical airflow and reduce plant density in current bench.",
            "Apply protective bio-fungicide (e.g. Bacillus subtilis formulation).",
            "Monitor rootzone drainage and moderate high-nitrogen vegetative feeding.",
        ],
    },
    "fenugreek_healthy": {
        "crop": "Fenugreek",
        "disease": "Healthy",
        "is_healthy": True,
        "recommendations": [
            "Vibrant trifoliate leaf development with zero visible necrotic lesions.",
            "Maintain optimal nutrient solution EC (1.4 - 1.8 mS/cm) and pH (6.0 - 6.8).",
            "Maintain standard light level and regular optical camera inspection.",
        ],
    },
}


class AIService:
    """
    AIService provides real-time plant disease classification and optical camera monitoring.
    Loads MobileNetV3-Small classifier once at startup as a singleton.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.uncertainty_threshold: float = settings.AI_UNCERTAINTY_THRESHOLD
        self.mean: List[float] = [0.485, 0.456, 0.406]
        self.std: List[float] = [0.229, 0.224, 0.225]
        self.padding_color: Tuple[int, int, int] = (124, 116, 104) # ImageNet mean RGB
        self.class_names: List[str] = CLASS_NAMES
        self.transform = None

        self._load_model()

    def _load_model(self):
        """Loads model weights and configuration once into memory."""
        model_path = Path(settings.AI_MODEL_PATH)
        metadata_path = Path(settings.AI_METADATA_PATH)

        if metadata_path.exists():
            try:
                with metadata_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.uncertainty_threshold = meta.get(
                        "uncertainty_threshold", self.uncertainty_threshold
                    )
                    norm = meta.get("normalization", {})
                    self.mean = norm.get("mean", self.mean)
                    self.std = norm.get("std", self.std)
                    if "class_names" in meta:
                        self.class_names = meta["class_names"]
            except Exception as e:
                logger.warning(f"Failed to read model metadata: {e}")

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=self.mean, std=self.std),
        ])

        if model_path.exists():
            try:
                checkpoint = torch.load(
                    model_path, map_location=self.device, weights_only=False
                )
                m = models.mobilenet_v3_small(weights=None)
                in_features = m.classifier[3].in_features
                m.classifier[3] = nn.Linear(in_features, len(self.class_names))
                m.load_state_dict(checkpoint["model_state_dict"])
                m.to(self.device)
                m.eval()
                self.model = m
                logger.info(
                    f"Successfully loaded MobileNetV3-Small plant disease model from {model_path} on {self.device}"
                )
            except Exception as e:
                logger.error(f"Failed to load plant disease model checkpoint: {e}")
                self.model = None
        else:
            logger.warning(
                f"Model checkpoint not found at {model_path}. Inference will fallback or report unavailable."
            )
            self.model = None

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Applies deterministic aspect-ratio-preserving fit to 224x224 with ImageNet-mean canvas padding.
        Matches the training pipeline exactly.
        """
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((224, 224), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (224, 224), self.padding_color)
        x = (224 - image.width) // 2
        y = (224 - image.height) // 2
        canvas.paste(image, (x, y))

        tensor = self.transform(canvas)
        return tensor.unsqueeze(0).to(self.device)

    def diagnose_image(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        user_id: str = "usr-default",
        farm_id: str = "farm-1",
        image_url: Optional[str] = None,
    ) -> ScanDiagnosisResponse:
        """
        Executes disease diagnosis inference on raw image bytes.
        """
        if not image_bytes:
            raise ValueError("Empty image data provided.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            raise ValueError(f"Corrupt or unsupported image format: {exc}")

        # Reopen after verify()
        image = Image.open(io.BytesIO(image_bytes))

        # Lazy re-load if model wasn't loaded initially
        if self.model is None:
            self._load_model()
            if self.model is None:
                raise RuntimeError("Diagnostic ML model is not available or failed to load.")

        input_tensor = self.preprocess_image(image)

        with torch.no_grad():
            logits = self.model(input_tensor)
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx = int(np.argmax(probabilities))
        pred_class = self.class_names[pred_idx]
        confidence = float(probabilities[pred_idx])

        # Top 3 predictions
        top3_indices = np.argsort(probabilities)[::-1][:3]
        top_predictions: List[PredictionDetail] = []
        for idx in top3_indices:
            cls_name = self.class_names[idx]
            info = CROP_MAPPING.get(cls_name, {"crop": "Unknown", "disease": cls_name, "is_healthy": False})
            top_predictions.append(
                PredictionDetail(
                    class_name=cls_name,
                    crop=info["crop"],
                    disease=info["disease"],
                    is_healthy=info["is_healthy"],
                    confidence=round(float(probabilities[idx]) * 100, 1),
                )
            )

        crop_info = CROP_MAPPING.get(
            pred_class,
            {"crop": "Unknown", "disease": pred_class, "is_healthy": False, "recommendations": []},
        )

        is_uncertain = confidence < self.uncertainty_threshold
        uncertainty_msg = None
        if is_uncertain:
            uncertainty_msg = (
                f"Prediction confidence ({confidence * 100:.1f}%) is below the diagnostic threshold "
                f"({self.uncertainty_threshold * 100:.0f}%). Symptoms may be early-stage or ambiguous. "
                "Manual agronomic confirmation recommended."
            )

        scan_id = f"scan-{uuid.uuid4().hex[:8]}"
        timestamp_str = time.strftime("Today, %I:%M %p")
        resolved_img_url = (
            image_url
            or f"https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600&scan={scan_id}"
        )

        # Store in database
        domain_scan = DomainAIScan(
            id=scan_id,
            farm_id=farm_id,
            user_id=user_id,
            plant_type=crop_info["crop"],
            disease_name=crop_info["disease"],
            is_healthy=crop_info["is_healthy"],
            confidence=round(confidence * 100, 1),
            image_url=resolved_img_url,
            timestamp=timestamp_str,
            recommendations=crop_info.get("recommendations", []),
        )
        db.scans[scan_id] = domain_scan

        return ScanDiagnosisResponse(
            id=scan_id,
            plantType=crop_info["crop"],
            diseaseName=crop_info["disease"],
            isHealthy=crop_info["is_healthy"],
            confidence=round(confidence * 100, 1),
            imageUrl=resolved_img_url,
            timestamp=timestamp_str,
            recommendations=crop_info.get("recommendations", []),
            predictedCrop=crop_info["crop"],
            predictedDisease=crop_info["disease"],
            rawClass=pred_class,
            isUncertain=is_uncertain,
            uncertaintyMessage=uncertainty_msg,
            topPredictions=top_predictions,
            thresholdApplied=self.uncertainty_threshold,
        )

    def get_scans(self, user_id: str) -> List[AIScan]:
        """
        Retrieves historical AI plant health diagnosis scans.
        """
        scans = [s for s in db.scans.values() if s.user_id == user_id or s.user_id == "usr-default"]
        # Return newest first
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
            for s in reversed(scans)
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
