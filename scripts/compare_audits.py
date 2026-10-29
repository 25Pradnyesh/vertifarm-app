#!/usr/bin/env python3
"""
scripts/compare_audits.py

Compares baseline_audit_test_predictions.csv and offline_aug_audit_test_predictions.csv
to provide a precise sample-by-sample audit for Phase A.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_CSV = ROOT / "models" / "baseline_audit_test_predictions.csv"
AUG_CSV = ROOT / "models" / "offline_aug_audit_test_predictions.csv"

def compare():
    with open(BASE_CSV, encoding="utf-8") as f:
        base_rows = list(csv.DictReader(f))

    with open(AUG_CSV, encoding="utf-8") as f:
        aug_rows = list(csv.DictReader(f))

    assert len(base_rows) == len(aug_rows) == 90

    agreed = 0
    disagreed = 0
    base_correct_aug_wrong = 0
    aug_correct_base_wrong = 0
    both_wrong = 0
    both_correct = 0

    disagreements = []

    for b, a in zip(base_rows, aug_rows):
        assert b["filename"] == a["filename"]
        assert b["true_class"] == a["true_class"]
        fname = b["filename"]
        true_cls = b["true_class"]
        b_pred = b["predicted_class"]
        a_pred = a["predicted_class"]
        b_corr = (b["is_correct"] == "True")
        a_corr = (a["is_correct"] == "True")
        b_conf = float(b["confidence"])
        a_conf = float(a["confidence"])

        if b_pred == a_pred:
            agreed += 1
            if b_corr:
                both_correct += 1
            else:
                both_wrong += 1
        else:
            disagreed += 1
            disagreements.append({
                "filename": fname,
                "true": true_cls,
                "base_pred": b_pred,
                "base_conf": b_conf,
                "base_corr": b_corr,
                "aug_pred": a_pred,
                "aug_conf": a_conf,
                "aug_corr": a_corr,
            })
            if b_corr and not a_corr:
                base_correct_aug_wrong += 1
            elif a_corr and not b_corr:
                aug_correct_base_wrong += 1
            else:
                both_wrong += 1

    print("=" * 70)
    print("PHASE A: SAMPLE-BY-SAMPLE PREDICTION COMPARISON")
    print("=" * 70)
    print(f"Total Test Samples: {len(base_rows)}")
    print(f"Prediction Agreement Rate: {agreed}/90 ({agreed/90*100:.2f}%)")
    print(f"Prediction Disagreements:  {disagreed}/90 ({disagreed/90*100:.2f}%)")
    print(f"Both Models Correct:       {both_correct}/90 ({both_correct/90*100:.2f}%)")
    print(f"Both Models Wrong:         {both_wrong}/90 ({both_wrong/90*100:.2f}%)")
    print(f"Baseline Correct, Aug Wrong (Regressions): {base_correct_aug_wrong}")
    print(f"Aug Correct, Baseline Wrong (Recoveries):  {aug_correct_base_wrong}")
    print("=" * 70)

    print("\nDETAILED DISAGREEMENTS ({} cases):".format(len(disagreements)))
    for d in disagreements:
        b_status = "CORRECT" if d["base_corr"] else "WRONG"
        a_status = "CORRECT" if d["aug_corr"] else "WRONG"
        print(f"\n* File: {d['filename']}")
        print(f"  Ground Truth: {d['true']}")
        print(f"  Baseline:     {d['base_pred']:<30} (conf: {d['base_conf']*100:.1f}%) -> {b_status}")
        print(f"  Augmented:    {d['aug_pred']:<30} (conf: {d['aug_conf']*100:.1f}%) -> {a_status}")

if __name__ == "__main__":
    compare()
