#!/usr/bin/env python3
"""
scripts/compare_three_way.py

3-Way Comparison:
- Baseline (EXP-001)
- Offline Augmented (EXP-004)
- Class-Weighted Regularized (EXP-005)
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load(fn):
    with open(ROOT / "models" / fn, encoding="utf-8") as f:
        return {r["filename"]: r for r in csv.DictReader(f)}

base = load("baseline_audit_test_predictions.csv")
aug = load("offline_aug_audit_test_predictions.csv")
cw = load("class_weighted_test_predictions.csv")

b_corr = sum(1 for r in base.values() if r["is_correct"] == "True")
a_corr = sum(1 for r in aug.values() if r["is_correct"] == "True")
cw_corr = sum(1 for r in cw.values() if r["is_correct"] == "True")

print("=" * 80)
print("THREE-WAY MODEL TEST EVALUATION COMPARISON (Held-Out Test Set N=90)")
print("=" * 80)
print(f"Baseline (EXP-001):          {b_corr}/90 correct ({b_corr/90*100:.2f}%)")
print(f"Offline Augmented (EXP-004): {a_corr}/90 correct ({a_corr/90*100:.2f}%)")
print(f"Class-Weighted (EXP-005):    {cw_corr}/90 correct ({cw_corr/90*100:.2f}%)")
print("=" * 80)

print("\nCORIANDER POWDERY MILDEW SAMPLES (15 Total):")
print(f"{'Filename':<42} {'Baseline':<10} {'Augmented':<10} {'Class-Weighted':<15}")
print("-" * 80)

pm_b = 0
pm_a = 0
pm_cw = 0

for fn in sorted(cw.keys()):
    r = cw[fn]
    if r["true_class"] == "coriander_powdery_mildew":
        b_c = (base[fn]["is_correct"] == "True")
        a_c = (aug[fn]["is_correct"] == "True")
        cw_c = (r["is_correct"] == "True")
        pm_b += int(b_c)
        pm_a += int(a_c)
        pm_cw += int(cw_c)
        b_s = "CORRECT" if b_c else "WRONG"
        a_s = "CORRECT" if a_c else "WRONG"
        cw_s = f"CORRECT ({float(r['confidence'])*100:.1f}%)" if cw_c else f"WRONG ({r['predicted_class'][:12]})"
        print(f"{fn[:40]:<42} {b_s:<10} {a_s:<10} {cw_s:<15}")

print("-" * 80)
print(f"Powdery Mildew Recall: Base={pm_b}/15 ({pm_b/15*100:.1f}%) | Aug={pm_a}/15 ({pm_a/15*100:.1f}%) | CW={pm_cw}/15 ({pm_cw/15*100:.1f}%)")

print("\nRECOVERIES BY EXP-005 (Cases where Baseline and/or Aug failed but CW succeeded):")
for fn in sorted(cw.keys()):
    r = cw[fn]
    b_c = (base[fn]["is_correct"] == "True")
    a_c = (aug[fn]["is_correct"] == "True")
    cw_c = (r["is_correct"] == "True")
    if cw_c and (not b_c or not a_c):
        print(f"* {fn} ({r['true_class']}): Base={'CORR' if b_c else 'FAIL'}, Aug={'CORR' if a_c else 'FAIL'} -> CW=CORRECT ({float(r['confidence'])*100:.1f}%)")

print("\nREMAINING MISCLASSIFICATIONS IN EXP-005 (7 Total):")
for fn in sorted(cw.keys()):
    r = cw[fn]
    if r["is_correct"] != "True":
        print(f"* {fn}: True={r['true_class']} -> Pred={r['predicted_class']} (conf: {float(r['confidence'])*100:.1f}%)")
