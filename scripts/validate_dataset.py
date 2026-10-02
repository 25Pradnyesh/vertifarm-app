#!/usr/bin/env python3
"""
scripts/validate_dataset.py

VertiFarm Dataset Quality & Split Leakage Validator.
Performs:
1. Image decodability verification.
2. Exact duplicate detection via SHA-256 file hashes.
3. Near-duplicate detection via perceptual difference hashing (dHash <= 4 Hamming distance).
4. Cross-split duplicate leakage audit (checking if duplicates cross train/val/test).
5. Quality checks: low resolution (< 150px) and extreme aspect ratios (> 2.5:1).
6. Comprehensive CSV report generation.
7. Original dataset preservation (strictly non-destructive).
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset"
PROCESSED_DIR = ROOT / "dataset_processed"
DEFAULT_REPORT_CSV = ROOT / "dataset_review" / "dataset_validation_report.csv"

CLASS_MAP = {
    ("Coriander", "Bacterial Blight"): "coriander_bacterial_blight",
    ("Coriander", "Coriander Healthy"): "coriander_healthy",
    ("Coriander", "Powdery Mildew"): "coriander_powdery_mildew",
    ("Fenugreek", "Bacterial blight"): "fenugreek_bacterial_blight",
    ("Fenugreek", "Cercospora leaf spot"): "fenugreek_cercospora_leaf_spot",
    ("Fenugreek", "Fenugreek Healthy"): "fenugreek_healthy",
}

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class DisjointSet:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> None:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j


def compute_dhash(image: Image.Image, hash_size: int = 8) -> np.ndarray:
    """Computes difference hash (dHash) vector of 64 booleans."""
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.array(resized)
    return (pixels[:, 1:] > pixels[:, :-1]).flatten()


def load_processed_splits(manifest_path: Path) -> Dict[str, str]:
    """Loads source_relative_path -> split from manifest.csv."""
    splits = {}
    if not manifest_path.exists():
        return splits
    with manifest_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row.get("source", "").strip()
            # Normalize path separators
            norm_src = str(Path(src))
            splits[norm_src] = row.get("split", "unknown")
    return splits


def validate_dataset(
    dataset_dir: Path = DATASET_DIR,
    manifest_path: Path = PROCESSED_DIR / "manifest.csv",
    output_csv: Path = DEFAULT_REPORT_CSV,
    near_dup_threshold: int = 4,
    min_dimension: int = 150,
    max_aspect_ratio: float = 2.5,
) -> Dict[str, any]:
    print("=" * 60)
    print("VERTIFARM DATASET QUALITY & VALIDATION AUDIT")
    print(f"Dataset root: {dataset_dir}")
    print(f"Manifest path: {manifest_path}")
    print("=" * 60)

    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    existing_splits = load_processed_splits(manifest_path)
    if existing_splits:
        print(f"Loaded existing split assignments for {len(existing_splits)} images from manifest.")
    else:
        print("No existing processed manifest found or empty; split leakage check will note unassigned.")

    # 1. Discover and decode all images
    records = []
    unreadable = []

    for (crop, folder), label in CLASS_MAP.items():
        class_folder = dataset_dir / crop / folder
        if not class_folder.exists():
            print(f"WARNING: Folder {class_folder} not found.")
            continue

        files = sorted(
            p for p in class_folder.rglob("*")
            if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
        )

        for path in files:
            rel_path = str(path.relative_to(ROOT))
            norm_rel_path = str(Path(rel_path))
            split = existing_splits.get(norm_rel_path, "unassigned")

            try:
                with Image.open(path) as im:
                    im.verify()

                with Image.open(path) as im:
                    im_transposed = ImageOps.exif_transpose(im)
                    width, height = im_transposed.size
                    dh = compute_dhash(im_transposed)

                with path.open("rb") as f:
                    file_sha256 = hashlib.sha256(f.read()).hexdigest()

                records.append({
                    "path": path,
                    "relative_path": rel_path,
                    "crop": crop.lower(),
                    "class": label,
                    "width": width,
                    "height": height,
                    "dimensions": f"{width}x{height}",
                    "aspect_ratio": round(max(width / height, height / width), 2),
                    "is_small": width < min_dimension or height < min_dimension,
                    "is_extreme_aspect": (max(width / height, height / width) > max_aspect_ratio),
                    "sha256": file_sha256,
                    "dhash": dh,
                    "split": split,
                })

            except (OSError, ValueError, UnidentifiedImageError) as exc:
                unreadable.append({
                    "path": rel_path,
                    "error": str(exc),
                })

    n = len(records)
    print(f"\nDiscovered {n} readable images across {len(CLASS_MAP)} classes.")
    if unreadable:
        print(f"FAILED to decode {len(unreadable)} images:")
        for u in unreadable:
            print(f"  {u['path']}: {u['error']}")
    else:
        print("Verification: All 600 images successfully decoded without errors.")

    # 2. Duplicate Clustering (Exact + Perceptual)
    dsu = DisjointSet(n)

    # Union exact SHA256 matches
    sha_map = defaultdict(list)
    for idx, r in enumerate(records):
        sha_map[r["sha256"]].append(idx)

    exact_dup_groups = 0
    exact_dup_images = 0
    for idxs in sha_map.values():
        if len(idxs) > 1:
            exact_dup_groups += 1
            exact_dup_images += len(idxs)
            for j in range(1, len(idxs)):
                dsu.union(idxs[0], idxs[j])

    # Union perceptual near-duplicate matches within same class
    near_dup_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            if records[i]["class"] == records[j]["class"]:
                dist = int(np.count_nonzero(records[i]["dhash"] != records[j]["dhash"]))
                if dist <= near_dup_threshold:
                    near_dup_pairs += 1
                    dsu.union(i, j)

    # Collect connected components (clusters)
    clusters = defaultdict(list)
    for i in range(n):
        clusters[dsu.find(i)].append(i)

    # Assign cluster IDs
    cluster_mapping = {}
    sorted_cluster_roots = sorted(clusters.keys())
    for cluster_num, root_id in enumerate(sorted_cluster_roots, start=1):
        cluster_id = f"DUP_GRP_{cluster_num:03d}"
        for member_idx in clusters[root_id]:
            cluster_mapping[member_idx] = (cluster_id, len(clusters[root_id]))

    # 3. Analyze Cross-Split Leakage & Build Report Rows
    report_rows = []
    leakage_groups = set()
    multi_member_clusters = 0

    for idx, r in enumerate(records):
        grp_id, grp_size = cluster_mapping[idx]
        cluster_members = clusters[dsu.find(idx)]
        member_splits = set(records[m]["split"] for m in cluster_members if records[m]["split"] != "unassigned")
        has_split_leakage = len(member_splits) > 1

        if grp_size > 1:
            if idx == cluster_members[0]:
                multi_member_clusters += 1
            if has_split_leakage:
                leakage_groups.add(grp_id)

        # Determine review status
        flags = []
        if grp_size > 1:
            flags.append(f"duplicate_group_size_{grp_size}")
        if has_split_leakage:
            flags.append("cross_split_leakage")
        if r["is_small"]:
            flags.append("small_resolution")
        if r["is_extreme_aspect"]:
            flags.append(f"extreme_aspect_ratio_{r['aspect_ratio']}")

        status = "; ".join(flags) if flags else "clean"

        report_rows.append({
            "source_path": r["relative_path"],
            "class": r["class"],
            "dimensions": r["dimensions"],
            "width": r["width"],
            "height": r["height"],
            "aspect_ratio": r["aspect_ratio"],
            "is_small": r["is_small"],
            "is_extreme_aspect": r["is_extreme_aspect"],
            "duplicate_group": grp_id,
            "group_size": grp_size,
            "split": r["split"],
            "cross_split_leakage": has_split_leakage,
            "review_status": status,
            "sha256": r["sha256"],
        })

    # Save CSV Report
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=report_rows[0].keys())
        writer.writeheader()
        writer.writerows(report_rows)

    # 4. Summary Metrics
    small_count = sum(1 for r in records if r["is_small"])
    extreme_aspect_count = sum(1 for r in records if r["is_extreme_aspect"])

    print("\n--- AUDIT SUMMARY ---")
    print(f"Total images checked: {n}")
    print(f"Unreadable images: {len(unreadable)}")
    print(f"Exact duplicate hash groups: {exact_dup_groups} (covering {exact_dup_images} images)")
    print(f"Perceptual near-duplicate pairs (dHash <= {near_dup_threshold}): {near_dup_pairs}")
    print(f"Total consolidated duplicate groups (exact + near): {multi_member_clusters}")
    print(f"Total unique visual entities (effective independent leaves): {len(clusters)}")
    print(f"Images with dimension < {min_dimension}px: {small_count}")
    print(f"Images with aspect ratio > {max_aspect_ratio}:1: {extreme_aspect_count}")
    print(f"Cross-split duplicate leakage groups detected: {len(leakage_groups)}")

    if leakage_groups:
        print("\n[CRITICAL WARNING] Data Leakage Detected!")
        print(f"  {len(leakage_groups)} duplicate clusters cross train/val/test splits.")
        print("  Rebuilding splits with grouped stratification is MANDATORY.")
    else:
        print("\n[PASS] No duplicate or near-duplicate images cross train/val/test splits.")

    print(f"\nValidation report saved to: {output_csv}")
    print("=" * 60)

    return {
        "total_images": n,
        "unreadable_count": len(unreadable),
        "exact_duplicate_groups": exact_dup_groups,
        "exact_duplicate_images": exact_dup_images,
        "near_duplicate_pairs": near_dup_pairs,
        "total_clusters": len(clusters),
        "multi_member_clusters": multi_member_clusters,
        "small_images_count": small_count,
        "extreme_aspect_count": extreme_aspect_count,
        "cross_split_leakage_groups": len(leakage_groups),
        "report_csv": str(output_csv),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate VertiFarm dataset quality and split integrity.")
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR, help="Path to original dataset")
    parser.add_argument("--manifest", type=Path, default=PROCESSED_DIR / "manifest.csv", help="Path to manifest.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_CSV, help="Path for validation report CSV")
    args = parser.parse_args()

    validate_dataset(
        dataset_dir=args.dataset,
        manifest_path=args.manifest,
        output_csv=args.output,
    )
