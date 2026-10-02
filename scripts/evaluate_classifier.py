#!/usr/bin/env python3
"""
scripts/evaluate_classifier.py

Evaluates the trained MobileNetV3-Small classifier on the held-out test set (dataset_processed/test).
Produces:
1. Test accuracy, macro/weighted precision, recall, F1-scores.
2. Per-class metrics breakdown with sample support.
3. Confusion matrix (text display and JSON).
4. Full test predictions CSV (image path, true label, predicted label, confidence, top 3).
5. Detailed list of misclassifications for agronomic analysis.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / "dataset_processed" / "test"
MODELS_DIR = ROOT / "models"
CHECKPOINT_PATH = MODELS_DIR / "mobilenet_v3_small_plant_disease.pth"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

CROP_MAPPING = {
    "coriander_bacterial_blight": {"crop": "Coriander", "disease": "Bacterial Blight", "is_healthy": False},
    "coriander_healthy": {"crop": "Coriander", "disease": "Healthy", "is_healthy": True},
    "coriander_powdery_mildew": {"crop": "Coriander", "disease": "Powdery Mildew", "is_healthy": False},
    "fenugreek_bacterial_blight": {"crop": "Fenugreek", "disease": "Bacterial Blight", "is_healthy": False},
    "fenugreek_cercospora_leaf_spot": {"crop": "Fenugreek", "disease": "Cercospora Leaf Spot", "is_healthy": False},
    "fenugreek_healthy": {"crop": "Fenugreek", "disease": "Healthy", "is_healthy": True},
}


def load_model(checkpoint_path: Path, device: torch.device) -> nn.Module:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, len(CLASS_NAMES))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model


def evaluate_test_set(
    test_dir: Path = TEST_DIR,
    checkpoint_path: Path = CHECKPOINT_PATH,
    output_dir: Path = MODELS_DIR,
    uncertainty_threshold: float = 0.60,
) -> Dict[str, any]:
    print("=" * 65)
    print("VERTIFARM CLASSIFIER HELD-OUT TEST EVALUATION")
    print(f"Test directory: {test_dir}")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"Uncertainty threshold: {uncertainty_threshold:.2f}")
    print("=" * 65)

    if not test_dir.exists():
        raise FileNotFoundError(f"Test set directory not found: {test_dir}")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load metadata if exists
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            meta = json.load(f)
            mean = meta.get("normalization", {}).get("mean", mean)
            std = meta.get("normalization", {}).get("std", std)
            uncertainty_threshold = meta.get("uncertainty_threshold", uncertainty_threshold)

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])

    test_dataset = ImageFolder(root=str(test_dir), transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)

    model = load_model(checkpoint_path, device)

    all_targets = []
    all_preds = []
    all_probs = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            all_targets.extend(labels.numpy())
            all_preds.extend(preds)
            all_probs.extend(probs)

    all_targets = np.array(all_targets)
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)

    # 1. Overall Metrics
    test_accuracy = accuracy_score(all_targets, all_preds)
    macro_precision = precision_score(all_targets, all_preds, average="macro", zero_division=0)
    macro_recall = recall_score(all_targets, all_preds, average="macro", zero_division=0)
    macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)

    # 2. Confusion Matrix
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(len(CLASS_NAMES))))

    # 3. Per-Class Metrics
    per_class_precision = precision_score(all_targets, all_preds, average=None, zero_division=0)
    per_class_recall = recall_score(all_targets, all_preds, average=None, zero_division=0)
    per_class_f1 = f1_score(all_targets, all_preds, average=None, zero_division=0)
    class_counts = np.bincount(all_targets, minlength=len(CLASS_NAMES))

    # 4. Detailed Predictions CSV & Misclassifications List
    predictions_rows = []
    misclassified = []

    for i, (img_path, label_idx) in enumerate(test_dataset.samples):
        pred_idx = all_preds[i]
        probs = all_probs[i]
        top3_indices = np.argsort(probs)[::-1][:3]
        confidence = float(probs[pred_idx])

        true_class = CLASS_NAMES[label_idx]
        pred_class = CLASS_NAMES[pred_idx]
        is_correct = bool(label_idx == pred_idx)
        is_uncertain = bool(confidence < uncertainty_threshold)

        crop_info = CROP_MAPPING[pred_class]

        top_3_str = "; ".join([
            f"{CLASS_NAMES[idx]}: {probs[idx]*100:.1f}%"
            for idx in top3_indices
        ])

        row = {
            "index": i + 1,
            "filename": Path(img_path).name,
            "source_path": str(Path(img_path).relative_to(ROOT)),
            "true_class": true_class,
            "predicted_class": pred_class,
            "predicted_crop": crop_info["crop"],
            "predicted_disease": crop_info["disease"],
            "is_healthy": crop_info["is_healthy"],
            "confidence": round(confidence, 4),
            "confidence_percent": f"{confidence * 100:.1f}%",
            "is_correct": is_correct,
            "is_uncertain": is_uncertain,
            "top_3_predictions": top_3_str,
        }
        predictions_rows.append(row)

        if not is_correct:
            misclassified.append({
                "filename": Path(img_path).name,
                "source_path": str(Path(img_path).relative_to(ROOT)),
                "true_class": true_class,
                "predicted_class": pred_class,
                "confidence": round(confidence, 4),
                "top_predictions": [
                    {"class": CLASS_NAMES[idx], "prob": round(float(probs[idx]), 4)}
                    for idx in top3_indices
                ],
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_csv_path = output_dir / "test_predictions.csv"
    with predictions_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=predictions_rows[0].keys())
        writer.writeheader()
        writer.writerows(predictions_rows)

    misclassified_json_path = output_dir / "misclassified_examples.json"
    with misclassified_json_path.open("w", encoding="utf-8") as f:
        json.dump(misclassified, f, indent=2)

    cm_json_path = output_dir / "confusion_matrix.json"
    with cm_json_path.open("w", encoding="utf-8") as f:
        json.dump({
            "class_names": CLASS_NAMES,
            "confusion_matrix": cm.tolist(),
        }, f, indent=2)

    # Print Report
    print("\n" + "=" * 65)
    print("TEST EVALUATION RESULTS SUMMARY")
    print("=" * 65)
    print(f"Total Test Samples: {len(all_targets)}")
    print(f"Test Accuracy:      {test_accuracy * 100:.2f}%")
    print(f"Macro Precision:    {macro_precision:.4f}")
    print(f"Macro Recall:       {macro_recall:.4f}")
    print(f"Macro F1-Score:     {macro_f1:.4f}")
    print(f"Weighted F1-Score:  {weighted_f1:.4f}")
    print(f"Misclassified Count:{len(misclassified)} / {len(all_targets)}")

    print("\n--- PER-CLASS PERFORMANCE ---")
    print(f"{'Class Name':<32} {'Support':<8} {'Precision':<10} {'Recall':<10} {'F1-Score':<10}")
    print("-" * 70)
    for c_idx, c_name in enumerate(CLASS_NAMES):
        print(
            f"{c_name:<32} {class_counts[c_idx]:<8} "
            f"{per_class_precision[c_idx]:<10.4f} {per_class_recall[c_idx]:<10.4f} "
            f"{per_class_f1[c_idx]:<10.4f}"
        )

    print("\n--- CONFUSION MATRIX ---")
    header_indices = "   " + " ".join([f"[{i}]" for i in range(len(CLASS_NAMES))])
    print(header_indices)
    for i, row in enumerate(cm):
        row_str = " ".join([f"{val:3d}" for val in row])
        print(f"[{i}] {row_str}   <- {CLASS_NAMES[i]}")

    if misclassified:
        print(f"\n--- MISCLASSIFIED EXAMPLES ({len(misclassified)}) ---")
        for m in misclassified:
            print(f"  * {m['filename']}: True={m['true_class']} -> Pred={m['predicted_class']} (conf: {m['confidence']*100:.1f}%)")
    else:
        print("\n--- ZERO MISCLASSIFICATIONS (100% Accuracy on Held-Out Test Set) ---")

    print("\n" + "=" * 65)
    print("SAVED ARTIFACTS:")
    print(f"  * Predictions CSV:   {predictions_csv_path}")
    print(f"  * Misclassified:     {misclassified_json_path}")
    print(f"  * Confusion Matrix:  {cm_json_path}")
    print("=" * 65)

    return {
        "test_accuracy": test_accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "total_test_samples": len(all_targets),
        "misclassified_count": len(misclassified),
        "confusion_matrix": cm.tolist(),
        "predictions_csv": str(predictions_csv_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate plant disease classifier on held-out test set.")
    parser.add_argument("--test-dir", type=Path, default=TEST_DIR, help="Path to test set directory")
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_PATH, help="Path to model checkpoint")
    parser.add_argument("--output", type=Path, default=MODELS_DIR, help="Output directory")
    parser.add_argument("--threshold", type=float, default=0.60, help="Uncertainty threshold")
    args = parser.parse_args()

    evaluate_test_set(
        test_dir=args.test_dir,
        checkpoint_path=args.checkpoint,
        output_dir=args.output,
        uncertainty_threshold=args.threshold,
    )
