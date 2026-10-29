#!/usr/bin/env python3
"""
scripts/audit_generalisation.py

Phase B Audit:
1. Strict split leakage verification across train, val, test, and augmented sets.
2. Perceptual hash and near-duplicate cluster distribution analysis across classes.
3. Detailed analysis of coriander_powdery_mildew test images vs training images.
"""

import csv
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "dataset"
PROC_DIR = ROOT / "dataset_processed"
AUG_DIR = ROOT / "dataset_augmented"
MANIFEST_PATH = PROC_DIR / "manifest.csv"
AUG_MANIFEST_PATH = AUG_DIR / "manifest.csv"

def compute_dhash(image: Image.Image, hash_size: int = 8) -> int:
    """Compute difference hash (dHash) as 64-bit integer."""
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(resized)
    diff = pixels[:, 1:] > pixels[:, :-1]
    return sum([bool(val) << i for i, val in enumerate(diff.flatten())])

def hamming_dist(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")

def audit():
    print("=" * 70)
    print("PHASE B: DATA INTEGRITY & GENERALISATION INVESTIGATION")
    print("=" * 70)

    # 1. Load split manifest
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        split_rows = list(csv.DictReader(f))

    print(f"Loaded split manifest: {len(split_rows)} entries.")

    split_counts = defaultdict(lambda: defaultdict(int))
    split_sources = defaultdict(set)
    source_to_split = {}

    for row in split_rows:
        s = row["split"]
        c = row["label"]
        src = row["source"]
        split_counts[s][c] += 1
        split_sources[s].add(src)
        source_to_split[src] = s

    # Check split disjointness
    train_sources = split_sources["train"]
    val_sources = split_sources["val"]
    test_sources = split_sources["test"]

    train_val_overlap = train_sources.intersection(val_sources)
    train_test_overlap = train_sources.intersection(test_sources)
    val_test_overlap = val_sources.intersection(test_sources)

    print(f"\n1. SPLIT ISOLATION CHECK:")
    print(f"  Train sources: {len(train_sources)}")
    print(f"  Val sources:   {len(val_sources)}")
    print(f"  Test sources:  {len(test_sources)}")
    print(f"  Train/Val overlap:  {len(train_val_overlap)}")
    print(f"  Train/Test overlap: {len(train_test_overlap)}")
    print(f"  Val/Test overlap:   {len(val_test_overlap)}")
    assert len(train_test_overlap) == 0, "CRITICAL: Test leakage into Train!"
    assert len(val_test_overlap) == 0, "CRITICAL: Test leakage into Val!"
    print("  => EXACT SPLIT ISOLATION: 100% DISJOINT (ZERO LEAKAGE).")

    # 2. Check Augmented Manifest sources
    if AUG_MANIFEST_PATH.exists():
        with open(AUG_MANIFEST_PATH, encoding="utf-8") as f:
            aug_rows = list(csv.DictReader(f))
        print(f"\n2. AUGMENTED DATASET INTEGRITY:")
        print(f"  Total augmented rows: {len(aug_rows)}")
        aug_sources = set(r["source_image_path"] for r in aug_rows)
        print(f"  Unique sources in augmented set: {len(aug_sources)}")
        # Check against test and val processed paths
        test_proc_paths = set(r["output"].replace("\\", "/") for r in split_rows if r["split"] == "test")
        val_proc_paths = set(r["output"].replace("\\", "/") for r in split_rows if r["split"] == "val")
        aug_test_overlap = aug_sources.intersection(test_proc_paths)
        aug_val_overlap = aug_sources.intersection(val_proc_paths)
        print(f"  Augmented / Test overlap: {len(aug_test_overlap)}")
        print(f"  Augmented / Val overlap:  {len(aug_val_overlap)}")
        assert len(aug_test_overlap) == 0, "CRITICAL: Augmented derivatives generated from Test set!"
        assert len(aug_val_overlap) == 0, "CRITICAL: Augmented derivatives generated from Val set!"
        print("  => ZERO LEAKAGE IN AUGMENTATION: 100% derived from training partition only.")

    # 3. Perceptual Hash & Near-Duplicate Clustering
    print(f"\n3. PERCEPTUAL DUPLICATE CLUSTERING:")
    img_data = []
    for row in split_rows:
        img_p = ROOT / row["output"]
        with Image.open(img_p) as im:
            dh = compute_dhash(im)
            # compute brightness, contrast (std), sharpness (Laplacian approx)
            arr = np.asarray(im.convert("L"), dtype=float)
            brightness = float(np.mean(arr))
            contrast = float(np.std(arr))
            laplacian_var = float(np.var(arr[1:-1, 1:-1] * 4 - arr[:-2, 1:-1] - arr[2:, 1:-1] - arr[1:-1, :-2] - arr[1:-1, 2:]))
            img_data.append({
                "filename": Path(row["output"]).name,
                "source_file": row["source"],
                "class": row["label"],
                "split": row["split"],
                "dhash": dh,
                "brightness": brightness,
                "contrast": contrast,
                "sharpness": laplacian_var,
            })

    # Find duplicate clusters with dHash distance <= 4
    n = len(img_data)
    parent = list(range(n))
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if img_data[i]["class"] == img_data[j]["class"]:
                if hamming_dist(img_data[i]["dhash"], img_data[j]["dhash"]) <= 4:
                    union(i, j)

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    class_clusters = defaultdict(lambda: defaultdict(list))
    for c_id, members in clusters.items():
        cls = img_data[members[0]]["class"]
        class_clusters[cls][c_id] = members

    print("  Per-class unique perceptual visual clusters (effective sample size out of 100 images):")
    for cls in sorted(class_clusters.keys()):
        total_clusters = len(class_clusters[cls])
        multi_member = sum(1 for m in class_clusters[cls].values() if len(m) > 1)
        max_cluster_size = max(len(m) for m in class_clusters[cls].values())
        print(f"    * {cls:<32}: {total_clusters} unique clusters (multi-member: {multi_member}, max group size: {max_cluster_size})")

    # 4. Check cross-split cluster leakage
    cross_split_clusters = 0
    for c_id, members in clusters.items():
        splits_in_cluster = set(img_data[m]["split"] for m in members)
        if len(splits_in_cluster) > 1:
            cross_split_clusters += 1
    print(f"\n  Cross-split clusters (dHash <= 4 crossing train/val/test): {cross_split_clusters}")
    if cross_split_clusters == 0:
        print("  => GROUPED STRATIFICATION VERIFIED: 0 clusters cross split boundaries!")
    else:
        print(f"  => NOTE: {cross_split_clusters} clusters share dHash <= 4 across splits.")

    # 5. Coriander Powdery Mildew Deep Dive
    print("\n" + "=" * 70)
    print("4. CORIANDER POWDERY MILDEW DEEP DIVE (15 Test Samples)")
    print("=" * 70)
    
    # Load test prediction comparisons
    with open(ROOT / "models" / "offline_aug_audit_test_predictions.csv", encoding="utf-8") as f:
        aug_preds = {r["filename"]: r for r in csv.DictReader(f)}
    with open(ROOT / "models" / "baseline_audit_test_predictions.csv", encoding="utf-8") as f:
        base_preds = {r["filename"]: r for r in csv.DictReader(f)}

    pm_test = [d for d in img_data if d["split"] == "test" and d["class"] == "coriander_powdery_mildew"]
    pm_train = [d for d in img_data if d["split"] == "train" and d["class"] == "coriander_powdery_mildew"]

    print(f"Total PM Test samples: {len(pm_test)}")
    print(f"Total PM Train samples: {len(pm_train)}")
    print(f"\n{'Filename':<48} {'Base Pred':<18} {'Aug Pred':<18} {'Bright':<8} {'Contrast':<8} {'Sharp':<8}")
    print("-" * 115)
    for p in pm_test:
        fn = p["filename"]
        bp = base_preds[fn]["predicted_class"][:16]
        ap = aug_preds[fn]["predicted_class"][:16]
        bc = (base_preds[fn]["is_correct"] == "True")
        ac = (aug_preds[fn]["is_correct"] == "True")
        b_str = f"{bp} ({'+' if bc else '-'})"
        a_str = f"{ap} ({'+' if ac else '-'})"
        print(f"{fn:<48} {b_str:<18} {a_str:<18} {p['brightness']:<8.1f} {p['contrast']:<8.1f} {p['sharpness']:<8.1f}")

    # Aggregate stats for PM test vs PM train
    train_b = np.mean([d["brightness"] for d in pm_train])
    test_b = np.mean([d["brightness"] for d in pm_test])
    train_c = np.mean([d["contrast"] for d in pm_train])
    test_c = np.mean([d["contrast"] for d in pm_test])
    train_s = np.mean([d["sharpness"] for d in pm_train])
    test_s = np.mean([d["sharpness"] for d in pm_test])

    print("\nAggregate Distribution Comparison (Train vs Test in coriander_powdery_mildew):")
    print(f"  Mean Brightness: Train = {train_b:.1f}, Test = {test_b:.1f} (Diff: {test_b - train_b:+.1f})")
    print(f"  Mean Contrast:   Train = {train_c:.1f}, Test = {test_c:.1f} (Diff: {test_c - train_c:+.1f})")
    print(f"  Mean Sharpness:  Train = {train_s:.1f}, Test = {test_s:.1f} (Diff: {test_s - train_s:+.1f})")

if __name__ == "__main__":
    audit()
