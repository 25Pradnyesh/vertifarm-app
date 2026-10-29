#!/usr/bin/env python3
"""
scripts/error_analysis.py

Phase C: Deep weak-class error analysis.
Investigates all misclassifications in models/offline_aug_audit_test_predictions.csv
and models/baseline_audit_test_predictions.csv with specific focus on:
- coriander_powdery_mildew (8 misclassifications in aug model)
- coriander_bacterial_blight (3 regressions in aug model)
- fenugreek_cercospora_leaf_spot & fenugreek_healthy
"""

import csv
import json
from pathlib import Path
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / "dataset_processed" / "test"
MODELS_DIR = ROOT / "models"
BASE_CHECKPOINT = MODELS_DIR / "mobilenet_v3_small_plant_disease.pth"
AUG_CHECKPOINT = MODELS_DIR / "mobilenet_v3_small_offline_augmented.pth"

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

def load_eval_model(checkpoint_path: Path):
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, len(CLASS_NAMES))
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model

def analyze():
    print("=" * 75)
    print("PHASE C: DEEP WEAK-CLASS ERROR ANALYSIS & PROBABILITY PROFILING")
    print("=" * 75)

    base_model = load_eval_model(BASE_CHECKPOINT)
    aug_model = load_eval_model(AUG_CHECKPOINT)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Load misclassified files from augmented model
    with open(MODELS_DIR / "offline_aug_audit_misclassified_examples.json", encoding="utf-8") as f:
        aug_misc = json.load(f)

    with open(MODELS_DIR / "baseline_audit_misclassified_examples.json", encoding="utf-8") as f:
        base_misc = json.load(f)

    all_test_images = list(TEST_DIR.rglob("*.png"))
    image_dict = {p.name: p for p in all_test_images}

    report = []

    print(f"\nTotal Aug Misclassifications: {len(aug_misc)}")
    print(f"Total Base Misclassifications: {len(base_misc)}\n")

    for m in aug_misc:
        fn = m["filename"]
        img_p = image_dict[fn]
        true_cls = m["true_class"]
        pred_cls = m["predicted_class"]

        with Image.open(img_p) as pil_im:
            rgb_arr = np.array(pil_im.convert("RGB"))
            tensor_in = transform(pil_im).unsqueeze(0)

        # Image visual metrics
        r_mean = float(np.mean(rgb_arr[:, :, 0]))
        g_mean = float(np.mean(rgb_arr[:, :, 1]))
        b_mean = float(np.mean(rgb_arr[:, :, 2]))
        # High-luminance / glare fraction (pixels with R>180 and G>180 and B>180)
        glare_mask = (rgb_arr[:, :, 0] > 180) & (rgb_arr[:, :, 1] > 180) & (rgb_arr[:, :, 2] > 180)
        glare_pct = float(np.mean(glare_mask) * 100)
        # Green dominance ratio (G / (R + B + 1e-5))
        green_ratio = float(g_mean / (r_mean + b_mean + 1e-5))

        with torch.no_grad():
            b_out = base_model(tensor_in)
            b_probs = torch.softmax(b_out, dim=1).numpy()[0]
            a_out = aug_model(tensor_in)
            a_probs = torch.softmax(a_out, dim=1).numpy()[0]

        b_pred_idx = int(np.argmax(b_probs))
        a_pred_idx = int(np.argmax(a_probs))
        true_idx = CLASS_NAMES.index(true_cls)

        b_top2_idx = np.argsort(b_probs)[::-1][:2]
        a_top2_idx = np.argsort(a_probs)[::-1][:2]

        b_margin = float(b_probs[b_top2_idx[0]] - b_probs[b_top2_idx[1]])
        a_margin = float(a_probs[a_top2_idx[0]] - a_probs[a_top2_idx[1]])

        item = {
            "filename": fn,
            "true_class": true_cls,
            "aug_pred": pred_cls,
            "aug_conf": round(float(a_probs[a_pred_idx]), 4),
            "aug_true_prob": round(float(a_probs[true_idx]), 4),
            "aug_margin": round(a_margin, 4),
            "aug_is_confident": bool(a_probs[a_pred_idx] >= 0.70),
            "base_pred": CLASS_NAMES[b_pred_idx],
            "base_conf": round(float(b_probs[b_pred_idx]), 4),
            "base_true_prob": round(float(b_probs[true_idx]), 4),
            "base_margin": round(b_margin, 4),
            "base_correct": bool(b_pred_idx == true_idx),
            "r_mean": round(r_mean, 1),
            "g_mean": round(g_mean, 1),
            "b_mean": round(b_mean, 1),
            "glare_pct": round(glare_pct, 2),
            "green_ratio": round(green_ratio, 3),
            "all_aug_probs": {CLASS_NAMES[i]: round(float(a_probs[i]), 4) for i in range(len(CLASS_NAMES))},
        }
        report.append(item)

    # Sort report by true class
    report.sort(key=lambda x: (x["true_class"], x["filename"]))

    # Print analysis table
    print(f"{'Filename':<42} {'True Class':<24} {'Aug Pred (Conf)':<26} {'True Cls Prob':<14} {'Base Pred':<18} {'Type':<12}")
    print("-" * 140)
    for r in report:
        aug_str = f"{r['aug_pred'][:18]} ({r['aug_conf']*100:.1f}%)"
        true_prob_str = f"{r['aug_true_prob']*100:.1f}%"
        err_type = "CONFIDENT" if r['aug_is_confident'] else "BORDERLINE"
        base_status = "CORRECT" if r['base_correct'] else "WRONG"
        base_str = f"{r['base_pred'][:10]} ({base_status})"
        print(f"{r['filename'][:40]:<42} {r['true_class'][:22]:<24} {aug_str:<26} {true_prob_str:<14} {base_str:<18} {err_type:<12}")

    # Breakdown by category
    print("\n" + "=" * 75)
    print("DETAILED ERROR MODE BREAKDOWN")
    print("=" * 75)

    pm_errors = [r for r in report if r["true_class"] == "coriander_powdery_mildew"]
    print(f"\n1. CORIANDER POWDERY MILDEW ERRORS ({len(pm_errors)} out of 15 test samples):")
    for r in pm_errors:
        print(f"\n* Sample: {r['filename']}")
        print(f"  Predicted: {r['aug_pred']} ({r['aug_conf']*100:.1f}% conf, margin: {r['aug_margin']*100:.1f}%) | True class prob: {r['aug_true_prob']*100:.1f}%")
        print(f"  Baseline was: {r['base_pred']} ({'CORRECT' if r['base_correct'] else 'WRONG'}, {r['base_conf']*100:.1f}% conf)")
        print(f"  Color/Texture: R={r['r_mean']}, G={r['g_mean']}, B={r['b_mean']}, Glare={r['glare_pct']}%, GreenRatio={r['green_ratio']}")
        probs_sorted = sorted(r['all_aug_probs'].items(), key=lambda x: x[1], reverse=True)
        top3_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in probs_sorted[:3]])
        print(f"  Aug Softmax Distribution: {top3_str}")

    bb_errors = [r for r in report if r["true_class"] == "coriander_bacterial_blight"]
    print(f"\n2. CORIANDER BACTERIAL BLIGHT REGRESSIONS ({len(bb_errors)} samples):")
    for r in bb_errors:
        print(f"\n* Sample: {r['filename']}")
        print(f"  Predicted: {r['aug_pred']} ({r['aug_conf']*100:.1f}% conf) | True class prob: {r['aug_true_prob']*100:.1f}%")
        print(f"  Baseline was: {r['base_pred']} ({'CORRECT' if r['base_correct'] else 'WRONG'}, {r['base_conf']*100:.1f}% conf)")
        probs_sorted = sorted(r['all_aug_probs'].items(), key=lambda x: x[1], reverse=True)
        top3_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in probs_sorted[:3]])
        print(f"  Aug Softmax Distribution: {top3_str}")

    out_json = MODELS_DIR / "phase_c_error_analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved Phase C analysis to: {out_json}")

if __name__ == "__main__":
    analyze()
