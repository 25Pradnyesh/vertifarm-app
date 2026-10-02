import io
from pathlib import Path
from PIL import Image


def test_list_scans(client, auth_headers):
    response = client.get("/api/v1/ai/scans", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "diseaseName" in data[0]
    assert "confidence" in data[0]


def test_get_scan_by_id(client, auth_headers):
    response = client.get("/api/v1/ai/scans/scan-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "scan-1"
    assert data["diseaseName"] == "Leaf Spot"


def test_get_camera_status(client, auth_headers):
    response = client.get("/api/v1/ai/camera/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cameraId" in data
    assert "imageUrl" in data
    assert "isLive" in data


def test_trigger_camera_capture(client, auth_headers):
    response = client.post("/api/v1/ai/camera/capture", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["queued"] is True
    assert "job_id" in data


def test_diagnose_scan_file(client, auth_headers):
    """Test image file upload diagnosis with MobileNetV3 model."""
    # Create a synthetic 224x224 RGB test leaf image in-memory
    im = Image.new("RGB", (224, 224), color=(34, 139, 34)) # Forest green leaf color
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test_leaf.png", buf, "image/png")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers=auth_headers,
        files=files,
        data={"farm_id": "farm-1"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["predictedCrop"] in ("Coriander", "Fenugreek")
    assert "predictedDisease" in data
    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))
    assert "isHealthy" in data
    assert isinstance(data["isHealthy"], bool)
    assert "topPredictions" in data
    assert len(data["topPredictions"]) == 3
    assert "isUncertain" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1


def test_diagnose_scan_json_filepath(client, auth_headers):
    """Test diagnosis via local file path JSON request."""
    # Find any actual test image from processed dataset
    test_image_dir = Path(__file__).resolve().parent.parent.parent / "dataset_processed" / "test"
    sample_images = list(test_image_dir.rglob("*.png"))
    assert len(sample_images) > 0, "No processed test images found."

    sample_path = str(sample_images[0])
    payload = {
        "filePath": sample_path,
        "farmId": "farm-1",
    }
    response = client.post(
        "/api/v1/ai/scans/diagnose-json",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["predictedCrop"] in ("Coriander", "Fenugreek")
    assert len(data["topPredictions"]) == 3
    assert data["confidence"] > 0


def test_diagnose_scan_base64(client, auth_headers):
    """Test diagnosis via Base64 encoded image request."""
    im = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    b64_str = "data:image/png;base64," + io.BytesIO(buf.getvalue()).getvalue().hex() # Or standard b64
    import base64
    b64_data = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    payload = {
        "imageBase64": b64_data,
        "farmId": "farm-1",
    }
    response = client.post(
        "/api/v1/ai/scans/diagnose-json",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictedCrop" in data
    assert "topPredictions" in data
    assert len(data["topPredictions"]) == 3
    assert "thresholdApplied" in data


def test_diagnose_invalid_image(client, auth_headers):
    """Test safe handling of corrupt/non-image upload."""
    invalid_bytes = io.BytesIO(b"Not an image file - arbitrary text data")
    files = {"file": ("corrupted.png", invalid_bytes, "image/png")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers=auth_headers,
        files=files,
    )
    assert response.status_code == 400
    assert "Image decoding failed" in response.json()["detail"]


def test_diagnose_scan_unauthenticated(client):
    """Verify that diagnosis endpoint rejects requests without Bearer authentication."""
    im = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)
    files = {"file": ("test_leaf.jpg", buf, "image/jpeg")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        files=files,
    )
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]


def test_diagnose_scan_invalid_token(client):
    """Verify that diagnosis endpoint rejects requests with invalid tokens."""
    im = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)
    files = {"file": ("test_leaf.jpg", buf, "image/jpeg")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers={"Authorization": "Bearer invalid-tampered-token"},
        files=files,
    )
    assert response.status_code == 401
    assert "Invalid or expired authentication token" in response.json()["detail"]


def test_diagnose_scan_with_real_leaf_image(client, auth_headers):
    """Verify real leaf diagnosis on an actual dataset test sample."""
    test_image_dir = Path(__file__).resolve().parent.parent.parent / "dataset_processed" / "test"
    sample_images = list(test_image_dir.rglob("*.png"))
    assert len(sample_images) > 0, "No processed test images found."

    sample = sample_images[0]
    with open(sample, "rb") as f:
        files = {"file": (sample.name, f, "image/png")}
        response = client.post(
            "/api/v1/ai/scans/diagnose",
            headers=auth_headers,
            files=files,
            data={"farm_id": "farm-1"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["predictedCrop"] in ("Coriander", "Fenugreek")
    assert isinstance(data["confidence"], (int, float))
    assert data["confidence"] > 0
    assert "predictedDisease" in data
    assert len(data["topPredictions"]) == 3
    assert "isHealthy" in data


def test_diagnose_response_schema_completeness(client, auth_headers):
    """Verify all ScanDiagnosisResponse fields are present and correctly typed."""
    im = Image.new("RGB", (224, 224), color=(60, 180, 75))
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("leaf_schema_test.jpg", buf, "image/jpeg")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers=auth_headers,
        files=files,
    )
    assert response.status_code == 200
    data = response.json()

    # All required ScanDiagnosisResponse fields must be present
    required_fields = [
        "id", "plantType", "diseaseName", "isHealthy", "confidence",
        "imageUrl", "timestamp", "recommendations",
        "predictedCrop", "predictedDisease", "rawClass",
        "isUncertain", "topPredictions", "thresholdApplied",
    ]
    for field in required_fields:
        assert field in data, f"Missing required response field: {field}"

    # Type checks matching frontend ScanDiagnosisResponse contract
    assert isinstance(data["id"], str) and data["id"].startswith("scan-")
    assert isinstance(data["isHealthy"], bool)
    assert isinstance(data["confidence"], (int, float))
    assert 0 <= data["confidence"] <= 100
    assert isinstance(data["isUncertain"], bool)
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["thresholdApplied"], (int, float))
    assert 0 < data["thresholdApplied"] <= 1.0

    # rawClass must be a known model class
    valid_classes = [
        "coriander_bacterial_blight", "coriander_healthy", "coriander_powdery_mildew",
        "fenugreek_bacterial_blight", "fenugreek_cercospora_leaf_spot", "fenugreek_healthy",
    ]
    assert data["rawClass"] in valid_classes, f"Unknown rawClass: {data['rawClass']}"

    # topPredictions structure validation
    assert len(data["topPredictions"]) == 3
    for pred in data["topPredictions"]:
        assert "class_name" in pred
        assert "crop" in pred
        assert "disease" in pred
        assert "is_healthy" in pred
        assert "confidence" in pred
        assert isinstance(pred["confidence"], (int, float))
        assert 0 <= pred["confidence"] <= 100

    # Confidence values should sum to <= 100 (top-3 subset of softmax)
    total = sum(p["confidence"] for p in data["topPredictions"])
    assert total <= 100.1, f"Top-3 confidence total {total} exceeds 100%"


def test_diagnose_multipart_field_name_file(client, auth_headers):
    """Verify the endpoint requires the multipart field name 'file' (matching mobile FormData)."""
    im = Image.new("RGB", (100, 100), color=(0, 128, 0))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)

    # Wrong field name: should fail with 422 (FastAPI validation error)
    files = {"image": ("test.png", buf, "image/png")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers=auth_headers,
        files=files,
    )
    assert response.status_code == 422, (
        f"Expected 422 for wrong field name 'image', got {response.status_code}"
    )


def test_diagnose_prediction_confidence_range(client, auth_headers):
    """Verify confidence is a percentage (0-100), not a raw probability (0-1)."""
    im = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("range_test.png", buf, "image/png")}
    response = client.post(
        "/api/v1/ai/scans/diagnose",
        headers=auth_headers,
        files=files,
    )
    assert response.status_code == 200
    data = response.json()

    # Main confidence must be a percentage, not a raw 0-1 probability
    assert data["confidence"] > 1.0 or data["confidence"] == 0, (
        f"Confidence {data['confidence']} looks like raw probability, expected percentage"
    )
    # thresholdApplied is a raw probability (0-1)
    assert 0 < data["thresholdApplied"] <= 1.0
