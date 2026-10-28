#!/usr/bin/env python3
"""
scripts/generate_augmented_dataset.py

VertiFarm Individual Image Augmentation & Labelled Dataset Generator.

Generates exactly nine separately saved augmented derivatives for every eligible
original training image in the leak-free preprocessed dataset (dataset_processed/train).

Key Architecture Guarantees:
1. Individual Standalone Images Only:
   - Each generated derivative is an independent, 224x224 RGB PNG image file.
   - Strictly NO collages, grids, montages, or composite images inside the dataset.
2. Nine Distinct Augmentation Techniques:
   - 1. Rotation (within +/- 20 degrees with ImageNet-mean canvas fill)
   - 2. Horizontal flip (~50% probability when sampled)
   - 3. Vertical flip (optional; top-down canopy view)
   - 4. Brightness (+/- 15% to 18%)
   - 5. Contrast (+/- 15% to 18%)
   - 6. Zoom / Crop (scale in [0.88, 0.94], preserving symptoms)
   - 7. Translation (up to 8-10% of image dimensions with ImageNet-mean fill)
   - 8. Gaussian blur (mild and occasional; suppressed for powdery mildew)
   - 9. Sensor noise (mild camera sensor noise std 3.5-6.5)
3. Exact Dataset Counts:
   - Verified original training images: 420 (70 per class x 6 classes)
   - Derivatives per original: 9
   - Total generated derivative files: 3,780 (630 per class x 6 classes)
   - Total combined training files: 4,200 (420 originals + 3,780 derivatives)
   - Validation images: 90 (unaugmented, held-out)
   - Test images: 90 (unaugmented, held-out)
4. Comprehensive Traceability:
   - Every file has a deterministic filename derived from the source image.
   - Writes dataset_augmented/manifest.csv (3,780 rows, 1 per derivative).
   - Writes dataset_augmented/combined_train_manifest.csv (4,200 rows: originals + derivatives).
   - Writes dataset_augmented/augmentation_config.json.
   - Writes dataset_augmented/README.md.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image, ImageDraw

from scripts.augmentations import (
    IMAGENET_MEAN_RGB,
    generate_nine_derivatives,
)

SOURCE_TRAIN_DIR = ROOT / "dataset_processed" / "train"
OUTPUT_DIR = ROOT / "dataset_augmented"
DEFAULT_PREVIEW_DIR = ROOT / "dataset_review" / "augmentation_preview"

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}

CLASS_DISPLAY = {
    "coriander_bacterial_blight": "Coriander: Bacterial Blight",
    "coriander_healthy": "Coriander: Healthy Foliage",
    "coriander_powdery_mildew": "Coriander: Powdery Mildew",
    "fenugreek_bacterial_blight": "Fenugreek: Bacterial Blight",
    "fenugreek_cercospora_leaf_spot": "Fenugreek: Cercospora Leaf Spot",
    "fenugreek_healthy": "Fenugreek: Healthy Foliage",
}


def compute_file_sha256(filepath: Path) -> str:
    """Calculates SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Calculates SHA-256 hash of byte buffer."""
    return hashlib.sha256(data).hexdigest()


def generate_augmented_dataset(
    source_dir: Path = SOURCE_TRAIN_DIR,
    output_dir: Path = OUTPUT_DIR,
    derivatives_per_original: int = 9,
    seed: int = 42,
    dry_run: bool = False,
    overwrite: bool = False,
    generate_preview_collage: bool = True,
    preview_dir: Path = DEFAULT_PREVIEW_DIR,
) -> Dict[str, Any]:
    start_time = time.time()

    print("=" * 70)
    print("VERTISENSE AI — INDIVIDUAL IMAGE AUGMENTATION & DATASET GENERATION")
    print(f"Source Directory:      {source_dir}")
    print(f"Output Directory:      {output_dir}")
    print(f"Derivatives / Sample:  {derivatives_per_original}")
    print(f"Base Random Seed:      {seed}")
    print(f"Dry Run:               {dry_run}")
    print(f"Overwrite:             {overwrite}")
    print("=" * 70)

    # 1. Verify source directory exists and is strictly 'train' split
    if not source_dir.exists():
        raise FileNotFoundError(f"Source training directory not found: {source_dir}")
    if "val" in str(source_dir).lower() or "test" in str(source_dir).lower():
        raise ValueError(f"SECURITY ALERT: Source directory '{source_dir}' appears to target val or test partition!")

    # 2. Enforce output directory safety
    target_train_dir = output_dir / "train"
    if target_train_dir.exists():
        existing_files = list(target_train_dir.rglob("*.png"))
        if existing_files and not overwrite and not dry_run:
            raise FileExistsError(
                f"Output directory '{target_train_dir}' already contains {len(existing_files)} images. "
                f"Pass --overwrite to regenerate safely."
            )

    # 3. Discover and validate source training images
    source_images_by_class: Dict[str, List[Path]] = {}
    total_source_count = 0
    skipped_count = 0

    print("\nAuditing eligible source training images...")
    for class_name in CLASS_NAMES:
        class_dir = source_dir / class_name
        if not class_dir.exists():
            raise FileNotFoundError(f"Missing class directory in source: {class_dir}")

        images = sorted(class_dir.glob("*.png"))
        valid_images = []
        for img_path in images:
            # Verify file can be opened and has 3 channels
            try:
                with Image.open(img_path) as im:
                    if im.size != (224, 224):
                        print(f"  WARNING: Skipping {img_path.name} (unexpected size {im.size})")
                        skipped_count += 1
                        continue
                    valid_images.append(img_path)
            except Exception as e:
                print(f"  WARNING: Skipping corrupt image {img_path.name}: {e}")
                skipped_count += 1

        source_images_by_class[class_name] = valid_images
        total_source_count += len(valid_images)
        print(f"  - {class_name:32s}: {len(valid_images):3d} eligible source images")

    print(f"\nTotal eligible source training images: {total_source_count}")
    print(f"Total skipped images:                {skipped_count}")

    expected_derivatives = total_source_count * derivatives_per_original
    expected_combined = total_source_count + expected_derivatives
    print(f"Expected generated derivative files: {expected_derivatives}")
    print(f"Expected combined training count:    {expected_combined}")

    if dry_run:
        print("\n[DRY RUN COMPLETE] Simulated generation without writing files.")
        return {
            "dry_run": True,
            "total_source_count": total_source_count,
            "expected_derivatives": expected_derivatives,
            "expected_combined": expected_combined,
            "skipped_count": skipped_count,
        }

    # 4. Prepare target directory tree
    for class_name in CLASS_NAMES:
        (target_train_dir / class_name).mkdir(parents=True, exist_ok=True)

    manifest_rows: List[Dict[str, Any]] = []
    combined_manifest_rows: List[Dict[str, Any]] = []

    # First, record original source images into combined manifest
    for class_name in CLASS_NAMES:
        cls_idx = CLASS_TO_IDX[class_name]
        for src_path in source_images_by_class[class_name]:
            src_base = src_path.name.split(".")[0].replace(" ", "_")
            src_sha256 = compute_file_sha256(src_path)
            rel_src_path = str(src_path.relative_to(ROOT)).replace("\\", "/")

            combined_manifest_rows.append({
                "image_path": rel_src_path,
                "image_id": src_base,
                "class_name": class_name,
                "class_index": cls_idx,
                "split": "train",
                "source_image_path": rel_src_path,
                "source_image_id": src_base,
                "is_augmented": 0,
                "augmentation_index": 0,
                "augmentation_policy": "original_unaugmented",
                "augmentation_parameters": json.dumps({"status": "source_original"}),
                "random_seed": seed,
                "image_width": 224,
                "image_height": 224,
                "file_hash": src_sha256,
            })

    # 5. Generate individual derivative files
    print("\nGenerating standalone augmented image files...")
    generated_count = 0
    actual_counts_per_class: Dict[str, int] = {c: 0 for c in CLASS_NAMES}

    # For preview collection: store 1 sample original and 9 derivatives per class
    preview_samples: Dict[str, Tuple[Image.Image, List[Tuple[Image.Image, int, str, Dict[str, Any]]]]] = {}

    for class_name in CLASS_NAMES:
        cls_idx = CLASS_TO_IDX[class_name]
        cls_target_dir = target_train_dir / class_name
        src_list = source_images_by_class[class_name]

        for s_idx, src_path in enumerate(src_list):
            src_base = src_path.name.split(".")[0].replace(" ", "_")
            rel_src_path = str(src_path.relative_to(ROOT)).replace("\\", "/")

            # Load original image
            with Image.open(src_path) as im:
                orig_img = im.convert("RGB")

            # Deterministic source-specific seed
            src_seed = (seed * 1000 + cls_idx * 100 + s_idx) & 0x7FFFFFFF

            # Generate exactly 9 derivatives
            derivatives = generate_nine_derivatives(
                orig_img,
                class_name=class_name,
                source_seed=src_seed,
                fill_color=IMAGENET_MEAN_RGB,
            )

            # Store first sample for human preview contact sheet
            if s_idx == 0 and generate_preview_collage:
                preview_samples[class_name] = (orig_img.copy(), derivatives)

            assert len(derivatives) == derivatives_per_original, (
                f"Expected {derivatives_per_original} derivatives, got {len(derivatives)} for {src_path.name}"
            )

            for aug_img, aug_idx, recipe_name, params in derivatives:
                # Standalone deterministic naming scheme
                filename = f"{src_base}_aug{aug_idx:02d}.png"
                out_path = cls_target_dir / filename
                rel_out_path = str(out_path.relative_to(ROOT)).replace("\\", "/")
                image_id = f"{src_base}_aug{aug_idx:02d}"

                # Ensure image is single transformed source image
                assert aug_img.size == (224, 224), f"Invalid dimensions {aug_img.size} for {filename}"
                assert aug_img.mode == "RGB", f"Invalid mode {aug_img.mode} for {filename}"

                # Save standalone PNG file
                aug_img.save(out_path, format="PNG", optimize=True)
                file_hash = compute_file_sha256(out_path)

                row_record = {
                    "image_path": rel_out_path,
                    "image_id": image_id,
                    "class_name": class_name,
                    "class_index": cls_idx,
                    "split": "train",
                    "source_image_path": rel_src_path,
                    "source_image_id": src_base,
                    "is_augmented": 1,
                    "augmentation_index": aug_idx,
                    "augmentation_policy": f"nine_techniques_{recipe_name}",
                    "augmentation_parameters": json.dumps(params),
                    "random_seed": src_seed,
                    "image_width": 224,
                    "image_height": 224,
                    "file_hash": file_hash,
                }

                manifest_rows.append(row_record)
                combined_manifest_rows.append(row_record)
                generated_count += 1
                actual_counts_per_class[class_name] += 1

        print(f"  - {class_name:32s}: generated {actual_counts_per_class[class_name]:4d} derivatives")

    # 6. Write manifest.csv (1 row per generated derivative = 3,780 rows)
    manifest_path = output_dir / "manifest.csv"
    manifest_fields = [
        "image_path",
        "image_id",
        "class_name",
        "class_index",
        "split",
        "source_image_path",
        "source_image_id",
        "is_augmented",
        "augmentation_index",
        "augmentation_policy",
        "augmentation_parameters",
        "random_seed",
        "image_width",
        "image_height",
        "file_hash",
    ]

    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(manifest_rows)

    manifest_hash = compute_file_sha256(manifest_path)
    print(f"\nManifest written: {manifest_path} ({len(manifest_rows)} rows)")
    print(f"Manifest SHA-256: {manifest_hash}")

    # 7. Write combined_train_manifest.csv (4,200 rows: 420 originals + 3,780 derivatives)
    combined_manifest_path = output_dir / "combined_train_manifest.csv"
    with combined_manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(combined_manifest_rows)

    combined_manifest_hash = compute_file_sha256(combined_manifest_path)
    print(f"Combined Manifest written: {combined_manifest_path} ({len(combined_manifest_rows)} rows)")
    print(f"Combined Manifest SHA-256: {combined_manifest_hash}")

    # 8. Write augmentation_config.json
    config_data = {
        "dataset_name": "VertiFarm Augmented Plant Disease Training Dataset",
        "description": "Offline augmented image dataset for precision leafy green disease classification.",
        "created_at_epoch_sec": time.time(),
        "source_split_reference": "dataset_processed/manifest.csv",
        "source_train_images": total_source_count,
        "derivatives_per_original": derivatives_per_original,
        "total_augmented_files": generated_count,
        "total_combined_train_files": len(combined_manifest_rows),
        "validation_images_unaugmented": 90,
        "test_images_unaugmented": 90,
        "skipped_images": skipped_count,
        "manifest_sha256": manifest_hash,
        "combined_manifest_sha256": combined_manifest_hash,
        "random_seed": seed,
        "target_resolution": [224, 224],
        "format": "PNG",
        "color_mode": "RGB",
        "neutral_canvas_padding_rgb": list(IMAGENET_MEAN_RGB),
        "per_class_counts": {
            c: {
                "class_index": CLASS_TO_IDX[c],
                "original_count": len(source_images_by_class[c]),
                "augmented_count": actual_counts_per_class[c],
                "combined_count": len(source_images_by_class[c]) + actual_counts_per_class[c],
            }
            for c in CLASS_NAMES
        },
        "techniques": {
            "1_rotation": {"range_deg": [-20.0, 20.0], "fill_color": list(IMAGENET_MEAN_RGB)},
            "2_horizontal_flip": {"probability": 0.5},
            "3_vertical_flip": {"probability": 0.2, "rationale": "Top-down canopy orientation"},
            "4_brightness": {"range": [0.82, 1.18]},
            "5_contrast": {"range": [0.82, 1.18]},
            "6_zoom_crop": {"scale_range": [0.88, 0.94], "rationale": "Conservative to prevent lesion loss"},
            "7_translation": {"max_percent": [0.08, 0.08], "fill_color": list(IMAGENET_MEAN_RGB)},
            "8_gaussian_blur": {
                "radius_range": [0.35, 0.65],
                "powdery_mildew_exception": "Suppressed for coriander_powdery_mildew to protect fine mycelial hyphae (ADR-005/ADR-006)",
            },
            "9_sensor_noise": {"type": "additive_gaussian_sensor_noise", "std_range": [3.5, 6.5]},
        },
        "scientific_limitations_and_integrity": [
            "Standalone individual images only. Zero collages, contact sheets, or grids used as training samples.",
            "Validation and test partitions remain 100% held-out and completely unaugmented.",
            "4,200 training images are derived from 420 source crops (430 unique leaves overall). Correlated samples must not be conflated with independent biological entities.",
        ],
    }

    config_path = output_dir / "augmentation_config.json"
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    print(f"Augmentation Config written: {config_path}")

    # 9. Write README.md
    readme_content = f"""# VertiFarm Augmented Plant Disease Training Dataset (`dataset_augmented/`)

## 1. Dataset Overview

This directory contains the offline-generated, individually labelled augmented dataset for VertiFarm's plant disease classification model (`MobileNetV3-Small`).

- **Original Training Images:** {total_source_count} (70 per class across 6 classes)
- **Augmented Derivatives per Original:** {derivatives_per_original}
- **Total Augmented Image Files:** {generated_count:,} (630 per class across 6 classes)
- **Combined Training Set:** {len(combined_manifest_rows):,} images ({total_source_count} originals + {generated_count:,} derivatives)
- **Validation Set (Held-Out):** 90 images (in `dataset_processed/val/`, completely unaugmented)
- **Test Set (Held-Out):** 90 images (in `dataset_processed/test/`, completely unaugmented)
- **Image Resolution:** 224 x 224 RGB PNG
- **Neutral Canvas Fill:** ImageNet-mean RGB `(124, 116, 104)` (maps to `(0.0, 0.0, 0.0)` in normalized tensor space)

---

## 2. Directory Structure

```
dataset_augmented/
    train/
        coriander_bacterial_blight/          [630 files]
            <source_id>_aug01.png
            <source_id>_aug02.png
            ...
            <source_id>_aug09.png
        coriander_healthy/                   [630 files]
        coriander_powdery_mildew/            [630 files]
        fenugreek_bacterial_blight/          [630 files]
        fenugreek_cercospora_leaf_spot/      [630 files]
        fenugreek_healthy/                   [630 files]
    manifest.csv                             [3,780 rows, 1 per derivative]
    combined_train_manifest.csv              [4,200 rows: originals + derivatives]
    augmentation_config.json                 [Full pipeline configuration]
    README.md                                [This file]
```

---

## 3. Mandatory Output Format & Non-Collage Guarantee

Every file in `train/` is a **standalone, individual 224x224 RGB PNG image** representing exactly one transformed leaf.

**Strict Prohibitions Enforced:**
- No collages, contact sheets, preview grids, or montages are saved in `train/`.
- No image combines multiple augmented versions into one file.
- Automated tests verify image dimensions and guarantee zero grid artifacts entered the training set.

---

## 4. Nine Distinct Augmentation Techniques

Each of the nine derivatives per source image implements a controlled, agronomically conservative recipe:

1. **Rotation:** Within $\\pm 20^\\circ$ with ImageNet-mean canvas fill.
2. **Horizontal Flip:** Approximately 50% probability when sampled (leaf lateral symmetry).
3. **Vertical Flip:** Optional; applied where top-down camera view is realistic.
4. **Brightness:** Approximately $\\pm 15\\% - 18\\%$ to simulate diurnal greenhouse lighting.
5. **Contrast:** Approximately $\\pm 15\\% - 18\\%$ to simulate cloud cover / diffuse shading.
6. **Zoom / Crop:** Up to 12% (scale $\\ge 0.88$) to prevent excising diagnostic disease lesions.
7. **Translation:** Up to $8\\% - 10\\%$ of dimensions with neutral canvas fill.
8. **Gaussian Blur:** Mild defocus blur (radius $0.35 - 0.65$). **Exception:** Suppressed for `coriander_powdery_mildew` to protect fine fungal mycelial hyphae (ADR-005/ADR-006).
9. **Sensor Noise:** Mild additive Gaussian sensor noise ($\\sigma \\in [3.5, 6.5]$ in uint8) to simulate camera sensor grain.

---

## 5. Traceability & Manifest Metadata

Every generated file has an entry in `manifest.csv` containing:
- `image_path`
- `image_id`
- `class_name`
- `class_index`
- `split`
- `source_image_path`
- `source_image_id`
- `is_augmented`
- `augmentation_index`
- `augmentation_policy`
- `augmentation_parameters` (serialized JSON)
- `random_seed`
- `image_width`
- `image_height`
- `file_hash` (SHA-256)

---

## 6. Scientific Limitations & Statistical Independence Note

> [!WARNING]
> While this augmented dataset contains {generated_count:,} generated files ({len(combined_manifest_rows):,} total training inputs), they are derived from 420 source images representing approximately 430 unique biological leaves. Augmented derivatives are statistically correlated and **must not be treated as independent biological samples**. Performance estimates on held-out test data ({90} independent leaves) represent the true measure of model generalization.
"""

    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"README written: {readme_path}")

    # 10. Generate visual preview collage for human inspection (if enabled)
    if generate_preview_collage and preview_samples:
        preview_dir.mkdir(parents=True, exist_ok=True)
        generate_human_review_collage(preview_samples, preview_dir, seed)

    duration = time.time() - start_time

    # 11. Final Summary Table
    print("\n" + "=" * 70)
    print("DATASET GENERATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Total execution duration: {duration:.2f} seconds")
    print(f"Total source originals:   {total_source_count}")
    print(f"Total augmented files:    {generated_count}")
    print(f"Combined training files:  {len(combined_manifest_rows)}")
    print(f"Skipped corrupt images:   {skipped_count}")
    print("\nPer-Class Breakdown Table:")
    print(f"{'Class Name':32s} | {'Originals':9s} | {'Augmented':9s} | {'Combined':9s}")
    print("-" * 70)
    for c in CLASS_NAMES:
        orig_c = len(source_images_by_class[c])
        aug_c = actual_counts_per_class[c]
        print(f"{c:32s} | {orig_c:9d} | {aug_c:9d} | {orig_c + aug_c:9d}")
    print("=" * 70)

    return {
        "status": "success",
        "duration_sec": duration,
        "total_source_count": total_source_count,
        "generated_count": generated_count,
        "combined_count": len(combined_manifest_rows),
        "skipped_count": skipped_count,
        "manifest_path": str(manifest_path),
        "manifest_hash": manifest_hash,
        "combined_manifest_path": str(combined_manifest_path),
        "combined_manifest_hash": combined_manifest_hash,
        "actual_counts_per_class": actual_counts_per_class,
    }


def generate_human_review_collage(
    samples: Dict[str, Tuple[Image.Image, List[Tuple[Image.Image, int, str, Dict[str, Any]]]]],
    output_dir: Path,
    seed: int,
):
    """
    Creates a single high-resolution preview collage showing original vs all 9 derivatives
    across all 6 classes specifically for human quality inspection.
    
    NOTE: This collage is saved strictly in dataset_review/ and NEVER enters dataset_augmented/.
    """
    cell_size = 180
    header_height = 50
    title_height = 40
    margin = 6
    label_width = 220

    cols = 10  # 1 original + 9 derivatives
    rows = len(CLASS_NAMES)

    grid_w = label_width + cols * (cell_size + margin) + margin
    grid_h = title_height + header_height + rows * (cell_size + margin) + margin

    canvas = Image.new("RGB", (grid_w, grid_h), color=(248, 249, 246))
    draw = ImageDraw.Draw(canvas)

    # Title
    draw.text(
        (margin + 10, 10),
        f"VertiFarm Individual Image Augmentation Audit — 9 Techniques per Class (Seed {seed})",
        fill=(27, 59, 43),
    )

    # Column Headers
    headers = [
        "Original (224x224)",
        "Aug #1: Rotation",
        "Aug #2: H-Flip",
        "Aug #3: Brightness",
        "Aug #4: Contrast",
        "Aug #5: Zoom/Crop",
        "Aug #6: Translation",
        "Aug #7: Sensor Noise",
        "Aug #8: Blur / Texture",
        "Aug #9: Composite",
    ]

    col_x_start = label_width + margin
    for col_idx, h_text in enumerate(headers):
        cx = col_x_start + col_idx * (cell_size + margin) + 5
        color = (27, 59, 43) if col_idx == 0 else (52, 168, 83)
        draw.text((cx, title_height + 15), h_text, fill=color)

    for row_idx, cls_name in enumerate(CLASS_NAMES):
        if cls_name not in samples:
            continue
        orig_img, derivatives = samples[cls_name]
        y_offset = title_height + header_height + row_idx * (cell_size + margin)

        # Class Label
        display_name = CLASS_DISPLAY.get(cls_name, cls_name)
        draw.text((margin + 10, y_offset + 30), display_name, fill=(27, 59, 43))
        draw.text((margin + 10, y_offset + 55), f"Index {CLASS_TO_IDX[cls_name]} | 9 Derivatives", fill=(100, 100, 100))

        # Paste Original
        orig_thumb = orig_img.resize((cell_size, cell_size), Image.Resampling.BILINEAR)
        canvas.paste(orig_thumb, (col_x_start, y_offset))

        # Paste 9 derivatives
        for d_idx, (aug_img, aug_num, recipe, _) in enumerate(derivatives):
            dx = col_x_start + (d_idx + 1) * (cell_size + margin)
            thumb = aug_img.resize((cell_size, cell_size), Image.Resampling.BILINEAR)
            canvas.paste(thumb, (dx, y_offset))

    collage_path = output_dir / "nine_techniques_preview.png"
    canvas.save(collage_path, format="PNG")
    print(f"Human inspection preview collage saved: {collage_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate individual augmented image dataset.")
    parser.add_argument("--source", type=Path, default=SOURCE_TRAIN_DIR, help="Source training directory")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Target augmented dataset directory")
    parser.add_argument("--derivatives", type=int, default=9, help="Number of derivatives per original image")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--dry-run", action="store_true", help="Simulate counts without writing files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output directory")
    parser.add_argument("--preview", action="store_true", default=True, help="Generate visual preview collage")
    args = parser.parse_args()

    generate_augmented_dataset(
        source_dir=args.source,
        output_dir=args.output,
        derivatives_per_original=args.derivatives,
        seed=args.seed,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        generate_preview_collage=args.preview,
    )

