# VertiFarm — Plant Disease Classification Model Report

## 1. Executive Summary

This report documents the dataset audit, quality verification, leak-free preprocessing, transfer learning training, test set evaluation, and backend integration of VertiFarm's first production plant disease classification model.

* **Model Architecture:** `MobileNetV3-Small` (pretrained on ImageNet-1K).
* **Task:** 6-class plant health and disease classification covering Coriander and Fenugreek crops.
* **Training Platform:** Windows, Python 3.12.10, PyTorch 2.14.0+cpu, Torchvision 0.29.0+cpu.
* **Held-Out Test Accuracy:** **85.56%** (Macro F1: **0.8517**, Weighted F1: **0.8517**).
* **Cross-Split Leakage:** **0%** (100% grouped isolation of exact and perceptual duplicates).
* **Backend Status:** Integrated into FastAPI backend with singleton model caching, multipart image upload, JSON/base64 support, and uncertainty handling.

---

## 2. Dataset Analysis & Quality Validation

### 2.1 Original Dataset Composition
The original dataset in `dataset/` comprises 600 images across 6 target classes (100 images per class):

| Crop | Original Folder Name | Unified Label | Image Count |
|---|---|---|---|
| Coriander | `Bacterial Blight` | `coriander_bacterial_blight` | 100 |
| Coriander | `Coriander Healthy` | `coriander_healthy` | 100 |
| Coriander | `Powdery Mildew` | `coriander_powdery_mildew` | 100 |
| Fenugreek | `Bacterial blight` | `fenugreek_bacterial_blight` | 100 |
| Fenugreek | `Cercospora leaf spot` | `fenugreek_cercospora_leaf_spot` | 100 |
| Fenugreek | `Fenugreek Healthy` | `fenugreek_healthy` | 100 |

### 2.2 Quality & Leakage Audit Findings
Running `scripts/validate_dataset.py` identified critical dataset characteristics:
1. **Decodability:** All 600 images decode successfully with 0 corrupt files.
2. **Exact Duplicates:** 99 exact SHA-256 duplicate hash groups covering 245 images.
3. **Perceptual Near-Duplicates:** 322 pairs with difference hash (dHash) Hamming distance $\le 4$.
4. **Independent Visual Entities:** 430 unique visual leaf entities across the 600 files.
5. **Class Contradictions:** **0** cross-class duplicates. All duplicates share identical class labels.
6. **Data Leakage in Previous Split:** 64 duplicate clusters had crossed `train`, `val`, and `test` splits in the previous naive random split, introducing synthetic overoptimism.
7. **Resolution Irregularities:** 111 images have at least one dimension $< 150\text{px}$, and 19 images have extreme aspect ratios ($> 2.5:1$ or $< 1:2.5$).

### 2.3 Leak-Free Stratified Group Splitting
To eliminate data leakage, `scripts/preprocess_dataset.py` groups all exact SHA-256 duplicates and perceptual near-duplicates into disjoint connected components before partitioning. A greedy bin-packing algorithm assigns entire clusters to splits, achieving an exact 70/15/15 target per class:

* **Train Split:** 420 images (70 per class)
* **Validation Split:** 90 images (15 per class)
* **Test Split:** 90 images (15 per class)
* **Cross-Split Leakage:** **0 clusters** (verified by `scripts/validate_dataset.py`).

---

## 3. Preprocessing & Padding Strategy

### 3.1 Input Dimension & Resizing
All inputs are transformed to $224 \times 224$ RGB tensors:
* **Orientation Correction:** EXIF transpose is applied before measurement.
* **Aspect-Ratio-Preserving Fit:** Images are resized using Lanczos resampling so the longer side fits within 224 pixels without stretching or warping leaf veins.

### 3.2 Documented Neutral Padding
Traditional letterboxing pastes images onto a black $(0, 0, 0)$ canvas. Because normalized ImageNet features expect natural scene color statistics, black margins normalize to severe negative values $(\approx -2.1, -2.0, -1.8)$, creating artificial high-frequency boundary edges.

**Strategy:** VertiFarm employs ImageNet-mean neutral RGB canvas padding $(124, 116, 104)$:
$$\text{mean}_{\text{ImageNet}} = [0.485 \times 255 \approx 124,\; 0.456 \times 255 \approx 116,\; 0.406 \times 255 \approx 104]$$
When transformed via `transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`, the padded border maps to $(0.0, 0.0, 0.0)$ in tensor space, generating zero artificial gradient activations.

### 3.3 Training Augmentation
To preserve subtle lesion patterns while preventing overfitting:
* `RandomHorizontalFlip(p=0.5)`
* `RandomVerticalFlip(p=0.5)`
* `RandomRotation(degrees=15)`
* `ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1)`
* Validation and Test sets receive only deterministic resizing and normalization.

---

## 4. Model Training & Configuration

* **Backbone:** `MobileNetV3-Small` (2.54M parameters).
* **Head:** `nn.Linear(1024, 6)` replacing the final ImageNet classification layer.
* **Loss Function:** `nn.CrossEntropyLoss()`
* **Optimizer:** `AdamW` with differential learning rates:
  * Backbone layers: $\text{lr} = 1 \times 10^{-4}$
  * Classification head: $\text{lr} = 5 \times 10^{-4}$
  * Weight decay: $1 \times 10^{-2}$
* **LR Schedule:** Cosine Annealing over 15 epochs ($\eta_{\min} = 1 \times 10^{-6}$).
* **Hardware:** Intel AMD64 CPU, batch size 32.
* **Duration:** 143.12 seconds (~2.39 minutes) for 14 epochs before early stopping.
* **Best Checkpoint:** Saved at **Epoch 8** based on Validation Macro F1 (**0.8566**, Accuracy **85.56%**).

---

## 5. Held-Out Test Evaluation Results

The best checkpoint was evaluated on the held-out test set ($N=90$, 15 images per class) using `scripts/evaluate_classifier.py`:

### 5.1 Overall Metrics
* **Test Accuracy:** **85.56%**
* **Macro Precision:** **0.8705**
* **Macro Recall:** **0.8556**
* **Macro F1-Score:** **0.8517**
* **Weighted F1-Score:** **0.8517**
* **Misclassified Samples:** 13 / 90

### 5.2 Per-Class Performance
| Class Name | Crop | Support | Precision | Recall | F1-Score |
|---|---|---|---|---|---|
| `coriander_bacterial_blight` | Coriander | 15 | 0.7895 | 1.0000 | **0.8824** |
| `coriander_healthy` | Coriander | 15 | 1.0000 | 0.9333 | **0.9655** |
| `coriander_powdery_mildew` | Coriander | 15 | 0.8000 | 0.5333 | **0.6400** |
| `fenugreek_bacterial_blight` | Fenugreek | 15 | 0.9333 | 0.9333 | **0.9333** |
| `fenugreek_cercospora_leaf_spot` | Fenugreek | 15 | 1.0000 | 0.8000 | **0.8889** |
| `fenugreek_healthy` | Fenugreek | 15 | 0.7000 | 0.9333 | **0.8000** |

### 5.3 Confusion Matrix
Rows represent true labels; columns represent model predictions:

```
                          [0]  [1]  [2]  [3]  [4]  [5]
[0] coriander_bacterial_blight  15    0    0    0    0    0
[1] coriander_healthy            1   14    0    0    0    0
[2] coriander_powdery_mildew     3    0    8    0    0    4
[3] fenugreek_bacterial_blight   0    0    0   14    0    1
[4] fenugreek_cercospora_leaf    0    0    1    1   12    1
[5] fenugreek_healthy            0    0    1    0    0   14
```

### 5.4 Error Analysis
* **Powdery Mildew Confusion:** The primary error source is `coriander_powdery_mildew` (7 of 15 misclassified). Analysis of the misclassified images reveals subtle, early-stage white fungal powder that closely mimics specular lighting reflections on healthy fenugreek or coriander leaves. Furthermore, powdery mildew in coriander had only 42 unique clusters in the source dataset, limiting variety.
* **Crop Disambiguation:** 84 of 90 test images (93.3%) were assigned to the correct crop family, confirming strong morphological feature separation between coriander and fenugreek.

---

## 6. Limitations & Calibration

1. **Preliminary Baseline Status:** The total dataset contains 600 images (430 unique visual leaves). Results should be treated as a proof-of-concept baseline rather than an exhaustive commercial diagnostic engine.
2. **Uncalibrated Softmax Probabilities:** Softmax outputs represent model ranking confidence rather than true Bayesian disease probability.
3. **Calibrated Uncertainty Threshold:** An uncertainty threshold of **0.60 (60.0%)** is enforced. Predictions below 60% confidence are explicitly flagged as uncertain (`isUncertain = true`) with a prompt recommending agronomist verification.
4. **Resolution Gaps:** Low-resolution web captures ($< 150\text{px}$) lose fine-grained fungal spore details. Real ESP32-CAM images should be captured with focused macro illumination.

---

## 7. Backend Integration Architecture

The model is integrated directly into the FastAPI backend (`backend/app/`):

### 7.1 Architecture & Endpoints
* **Singleton Service (`backend/app/services/ai_service.py`):** The MobileNetV3-Small checkpoint is loaded once into memory on startup and cached for all requests.
* **Multipart File Upload (`POST /api/v1/ai/scans/diagnose`):** Accepts standard image uploads (`UploadFile`), performs inference, persists the scan in session storage, and returns structured diagnosis.
* **JSON / Base64 Support (`POST /api/v1/ai/scans/diagnose-json`):** Accepts base64 image strings or local file paths for automated testing and edge pipelines.
* **Historical Queries (`GET /api/v1/ai/scans` & `GET /api/v1/ai/scans/{id}`):** Return historical diagnostic records including diagnosed images.

### 7.2 Response Contract
```json
{
  "id": "scan-e414fdb5",
  "plantType": "Coriander",
  "diseaseName": "Bacterial Blight",
  "isHealthy": false,
  "confidence": 98.4,
  "imageUrl": "https://images.unsplash.com/photo-1592417817098-8f3d6910a566?w=600&scan=scan-e414fdb5",
  "timestamp": "Today, 08:15 AM",
  "recommendations": [
    "Prune and dispose of severely infected leaves to prevent bacterial spread.",
    "Reduce canopy humidity by improving ventilation and plant spacing.",
    "Avoid overhead irrigation; transition to drip or targeted root watering.",
    "Apply copper-based bactericide or approved biological control spray."
  ],
  "predictedCrop": "Coriander",
  "predictedDisease": "Bacterial Blight",
  "rawClass": "coriander_bacterial_blight",
  "isUncertain": false,
  "uncertaintyMessage": null,
  "topPredictions": [
    {
      "class_name": "coriander_bacterial_blight",
      "crop": "Coriander",
      "disease": "Bacterial Blight",
      "is_healthy": false,
      "confidence": 98.4
    },
    {
      "class_name": "coriander_healthy",
      "crop": "Coriander",
      "disease": "Healthy",
      "is_healthy": true,
      "confidence": 1.2
    },
    {
      "class_name": "coriander_powdery_mildew",
      "crop": "Coriander",
      "disease": "Powdery Mildew",
      "is_healthy": false,
      "confidence": 0.4
    }
  ],
  "thresholdApplied": 0.6
}
```

### 7.3 Mobile Client Integration Architecture

The mobile presentation layer integrates with the inference backend through the following components:
1. **HTTP / Multipart Client (`services/apiClient.ts`):** `postMultipart<T>()` handles `FormData` image streaming while preserving boundary headers and injecting authentication tokens.
2. **AI Service Layer (`services/aiService.ts`):** `diagnoseImage()` bridges device image URIs (native file, base64 data URIs, or web blobs) to the `/ai/scans/diagnose` endpoint with offline fallback.
3. **Camera & Diagnostic Viewfinder (`app/ai/camera.tsx`):** Employs `expo-image-picker` for live camera captures and photo library uploads, offers preview target framing, sample leaf presets, and real-time inference progress indicators.
4. **Diagnostic Results Screen (`app/ai/result.tsx`):** Parses `ScanDiagnosisResponse` route payloads, renders color-coded health/disease badges, multi-class Softmax distribution bars, calibrated uncertainty warning banners ($< 0.60$), and actionable agronomic recommendations.

---

## 8. Execution Commands

### 8.1 Dataset Quality Validation
```bash
python scripts/validate_dataset.py
```

### 8.2 Dataset Preprocessing (Leak-Free Splitting)
```bash
python scripts/preprocess_dataset.py --overwrite
```

### 8.3 Model Training
```bash
python scripts/train_classifier.py --epochs 15 --batch-size 32 --lr 0.0005
```

### 8.4 Model Evaluation on Held-Out Test Set
```bash
python scripts/evaluate_classifier.py --threshold 0.60
```

### 8.5 Running Backend Tests
```bash
pytest backend/tests/test_scans.py
```

### 8.6 Running Inference via FastAPI Backend
Start the backend server:
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
Run diagnosis inference via cURL:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/scans/diagnose" \
  -H "Authorization: Bearer dev-token-usr-default" \
  -F "file=@dataset_processed/test/coriander_bacterial_blight/coriander_bacterial_blight_0001_Bacterial Blight.jpg.png"
```
Or run diagnosis via JSON file path:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/scans/diagnose-json" \
  -H "Authorization: Bearer dev-token-usr-default" \
  -H "Content-Type: application/json" \
  -d '{"filePath": "dataset_processed/test/fenugreek_healthy/fenugreek_healthy_0001_Fenugreek Healthy.jpg.png"}'
```
