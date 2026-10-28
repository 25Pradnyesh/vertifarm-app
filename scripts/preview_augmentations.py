#!/usr/bin/env python3
"""
scripts/preview_augmentations.py

Generates visual preview grids comparing original plant disease training images
with multiple stochastic augmented variants produced by the conservative pipeline.

Saves:
- Full 6-class comparison grid: dataset_review/augmentation_preview/augmentation_grid.png
- Per-class comparison strips:  dataset_review/augmentation_preview/<class>_preview.png
- Preview metadata report:     dataset_review/augmentation_preview/preview_manifest.json
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch

from scripts.augmentations import (
    AugmentationConfig,
    build_train_transforms,
    denormalize_tensor,
    get_augmentation_policy,
)

ROOT = Path(__file__).resolve().parent.parent
TRAIN_DIR = ROOT / "dataset_processed" / "train"
DEFAULT_OUTPUT_DIR = ROOT / "dataset_review" / "augmentation_preview"

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

CLASS_DISPLAY = {
    "coriander_bacterial_blight": "Coriander: Bacterial Blight",
    "coriander_healthy": "Coriander: Healthy Foliage",
    "coriander_powdery_mildew": "Coriander: Powdery Mildew",
    "fenugreek_bacterial_blight": "Fenugreek: Bacterial Blight",
    "fenugreek_cercospora_leaf_spot": "Fenugreek: Cercospora Leaf Spot",
    "fenugreek_healthy": "Fenugreek: Healthy Foliage",
}


def generate_previews(
    train_dir: Path = TRAIN_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    policy_name: str = "conservative",
    num_variants: int = 4,
    seed: int = 42,
) -> Dict[str, any]:
    print("=" * 65)
    print("VERTIFARM DATA AUGMENTATION PREVIEW GENERATOR")
    print(f"Source train directory: {train_dir}")
    print(f"Output directory:       {output_dir}")
    print(f"Augmentation policy:    {policy_name}")
    print(f"Variants per sample:    {num_variants}")
    print(f"Random seed:            {seed}")
    print("=" * 65)

    if not train_dir.exists():
        raise FileNotFoundError(f"Training directory not found: {train_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    config = get_augmentation_policy(policy_name)
    train_transforms = build_train_transforms(config)

    torch.manual_seed(seed)
    np.random.seed(seed)

    cell_size = 224
    header_height = 40
    title_height = 40
    margin = 8
    label_width = 240

    total_cols = 1 + num_variants  # Original + N variants
    grid_width = label_width + total_cols * (cell_size + margin) + margin
    grid_height = title_height + header_height + len(CLASS_NAMES) * (cell_size + margin) + margin

    # Canvas with clean off-white botanical background
    master_grid = Image.new("RGB", (grid_width, grid_height), color=(248, 249, 246))
    master_draw = ImageDraw.Draw(master_grid)

    # Master title
    master_draw.text(
        (margin + 10, 10),
        f"VertiFarm Augmentation Plausibility Audit — Policy: '{policy_name}' (Seed {seed})",
        fill=(27, 59, 43),  # Deep Forest Green
    )

    # Column headers
    col_x_start = label_width + margin
    master_draw.text((col_x_start + 10, title_height + 10), "Original Input (224x224)", fill=(27, 59, 43))
    for v in range(num_variants):
        vx = col_x_start + (v + 1) * (cell_size + margin) + 10
        master_draw.text((vx, title_height + 10), f"Augmented #{v + 1}", fill=(52, 168, 83))

    manifest_records = []

    for row_idx, cls_name in enumerate(CLASS_NAMES):
        cls_dir = train_dir / cls_name
        images = sorted(cls_dir.glob("*.png"))
        if not images:
            print(f"WARNING: No images found in {cls_dir}")
            continue

        # Deterministic sample selection based on seed
        sample_path = images[seed % len(images)]
        orig_img = Image.open(sample_path).convert("RGB")

        y_offset = title_height + header_height + row_idx * (cell_size + margin)

        # Row label
        display_label = CLASS_DISPLAY.get(cls_name, cls_name)
        master_draw.text((margin + 10, y_offset + 30), display_label, fill=(27, 59, 43))
        master_draw.text((margin + 10, y_offset + 55), sample_path.name[:28], fill=(120, 120, 120))
        master_draw.text((margin + 10, y_offset + 75), f"Crop: {cls_name.split('_')[0].capitalize()}", fill=(100, 100, 100))

        # Paste original
        master_grid.paste(orig_img, (col_x_start, y_offset))

        # Single strip for individual class
        strip_width = label_width + total_cols * (cell_size + margin) + margin
        strip_height = cell_size + margin * 2 + 30
        strip = Image.new("RGB", (strip_width, strip_height), color=(255, 255, 255))
        strip_draw = ImageDraw.Draw(strip)
        strip_draw.text((margin + 10, 12), display_label, fill=(27, 59, 43))
        strip.paste(orig_img, (col_x_start, margin + 20))

        variant_records = []

        # Generate stochastic variants
        for v_idx in range(num_variants):
            aug_tensor = train_transforms(orig_img)
            aug_img = denormalize_tensor(aug_tensor, mean=config.mean, std=config.std)

            px = col_x_start + (v_idx + 1) * (cell_size + margin)
            master_grid.paste(aug_img, (px, y_offset))
            strip.paste(aug_img, (px, margin + 20))

            variant_records.append({
                "variant_index": v_idx + 1,
                "tensor_shape": list(aug_tensor.shape),
                "tensor_min": round(float(aug_tensor.min()), 3),
                "tensor_max": round(float(aug_tensor.max()), 3),
            })

        # Save class strip
        strip_path = output_dir / f"{cls_name}_preview.png"
        strip.save(strip_path, format="PNG", optimize=True)

        manifest_records.append({
            "class_name": cls_name,
            "sample_file": sample_path.name,
            "display_name": display_label,
            "strip_path": str(strip_path.relative_to(ROOT)),
            "variants": variant_records,
        })

    # Save master grid
    grid_path = output_dir / "augmentation_grid.png"
    master_grid.save(grid_path, format="PNG", optimize=True)

    # Save manifest JSON
    manifest_path = output_dir / "preview_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump({
            "policy": policy_name,
            "seed": seed,
            "num_variants": num_variants,
            "grid_image": str(grid_path.relative_to(ROOT)),
            "classes": manifest_records,
        }, f, indent=2)

    print("\n" + "=" * 65)
    print("PREVIEW GENERATION COMPLETE")
    print(f"Master Grid Image: {grid_path}")
    print(f"Preview Manifest:  {manifest_path}")
    print(f"Total Classes Audited: {len(manifest_records)}")
    print("=" * 65)

    return {
        "grid_path": str(grid_path),
        "manifest_path": str(manifest_path),
        "class_count": len(manifest_records),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate data augmentation visual preview grids.")
    parser.add_argument("--train-dir", type=Path, default=TRAIN_DIR, help="Path to preprocessed train dir")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to save preview images")
    parser.add_argument("--policy", type=str, default="conservative", help="Augmentation policy name")
    parser.add_argument("--variants", type=int, default=4, help="Number of augmented variants per class")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible preview")
    args = parser.parse_args()

    generate_previews(
        train_dir=args.train_dir,
        output_dir=args.output,
        policy_name=args.policy,
        num_variants=args.variants,
        seed=args.seed,
    )
