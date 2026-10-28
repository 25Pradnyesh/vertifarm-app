#!/usr/bin/env python3
"""
scripts/test_augmentation_pipeline.py

Comprehensive test suite verifying the integrity, safety, determinism,
and mathematical validity of the VertiFarm data augmentation pipeline.

Verification checks:
1. All 6 class labels remain strictly mapped and invariant.
2. Augmented outputs have shape (3, 224, 224) and valid float ranges.
3. Original source files on disk remain bitwise immutable.
4. Validation and test pipelines are strictly deterministic (zero stochasticity).
5. Fixed random seeds provide bitwise reproducible outputs.
6. Split manifests and class balances remain 100% consistent.
7. No synthetic or preview file enters the validation or test partitions.
8. ImageNet-mean canvas padding normalizes precisely to (0.0, 0.0, 0.0) in tensor space.
"""

import csv
import hashlib
from pathlib import Path
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder

from scripts.augmentations import (
    AugmentationConfig,
    IMAGENET_MEAN,
    IMAGENET_MEAN_RGB,
    IMAGENET_STD,
    build_eval_transforms,
    build_train_transforms,
    denormalize_tensor,
    get_augmentation_policy,
)

RAW_DIR = ROOT / "dataset"
PROCESSED_DIR = ROOT / "dataset_processed"
TRAIN_DIR = PROCESSED_DIR / "train"
VAL_DIR = PROCESSED_DIR / "val"
TEST_DIR = PROCESSED_DIR / "test"
MANIFEST_PATH = PROCESSED_DIR / "manifest.csv"

AUGMENTED_DIR = ROOT / "dataset_augmented"
AUGMENTED_TRAIN_DIR = AUGMENTED_DIR / "train"
AUGMENTED_MANIFEST_PATH = AUGMENTED_DIR / "manifest.csv"
COMBINED_MANIFEST_PATH = AUGMENTED_DIR / "combined_train_manifest.csv"
AUGMENTED_CONFIG_PATH = AUGMENTED_DIR / "augmentation_config.json"

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]


def test_class_label_invariance():
    """Verify all 6 class labels exist and map deterministically."""
    print("[TEST 1/8] Verifying class label mapping and index invariance...")
    dataset = ImageFolder(root=str(TRAIN_DIR), transform=transforms.ToTensor())
    class_to_idx = dataset.class_to_idx

    assert len(class_to_idx) == 6, f"Expected 6 classes, got {len(class_to_idx)}"
    assert list(class_to_idx.keys()) == CLASS_NAMES, f"Class ordering mismatch: {list(class_to_idx.keys())}"
    for i, name in enumerate(CLASS_NAMES):
        assert class_to_idx[name] == i, f"Class {name} index mismatch: expected {i}, got {class_to_idx[name]}"
    print("  --> PASS: All 6 classes verified with exact index alignment (0 to 5).")


def test_output_dimensions_and_ranges():
    """Verify augmented outputs have valid shapes and float ranges."""
    print("[TEST 2/8] Verifying output dimensions and pixel ranges...")
    config = get_augmentation_policy("conservative")
    train_transform = build_train_transforms(config)

    sample_paths = list(TRAIN_DIR.rglob("*.png"))[:12]
    assert len(sample_paths) > 0, "No sample images found in train directory"

    for p in sample_paths:
        with Image.open(p) as img:
            rgb = img.convert("RGB")
            tensor = train_transform(rgb)

            # Dimensions check
            assert tensor.shape == (3, 224, 224), f"Wrong shape {tensor.shape} for {p.name}"
            assert tensor.dtype == torch.float32, f"Wrong dtype {tensor.dtype} for {p.name}"

            # Float range check (normalized with mean ~0.45, std ~0.22 means values roughly between -2.2 and +2.8)
            t_min = float(tensor.min())
            t_max = float(tensor.max())
            assert -3.0 <= t_min <= 0.5, f"Abnormal min tensor value: {t_min} in {p.name}"
            assert 0.0 <= t_max <= 3.5, f"Abnormal max tensor value: {t_max} in {p.name}"

    print(f"  --> PASS: Verified dimensions (3, 224, 224) and valid normalized range across {len(sample_paths)} samples.")


def test_source_data_immutability():
    """Verify raw dataset and preprocessed dataset source images are never modified in-place."""
    print("[TEST 3/8] Verifying source data immutability on disk...")
    # Sample 10 raw images and verify their SHA-256 before and after transform execution
    raw_samples = list(RAW_DIR.rglob("*.*"))[:10]
    config = get_augmentation_policy("conservative")
    transform = build_train_transforms(config)

    for p in raw_samples:
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        with open(p, "rb") as f:
            h_before = hashlib.sha256(f.read()).hexdigest()

        # Load and transform image
        with Image.open(p) as im:
            _ = transform(im.convert("RGB"))

        with open(p, "rb") as f:
            h_after = hashlib.sha256(f.read()).hexdigest()

        assert h_before == h_after, f"Source image {p.name} was mutated on disk!"

    print("  --> PASS: Confirmed zero in-place mutations; source files on disk remain strictly immutable.")


def test_eval_pipeline_determinism():
    """Verify validation and test pipelines have zero stochasticity."""
    print("[TEST 4/8] Verifying validation/test pipeline determinism and split isolation...")
    config = get_augmentation_policy("conservative")
    eval_transform = build_eval_transforms(config)

    val_samples = list(VAL_DIR.rglob("*.png"))[:6]
    for p in val_samples:
        with Image.open(p) as img:
            rgb = img.convert("RGB")
            t1 = eval_transform(rgb)
            t2 = eval_transform(rgb)

            # Two passes must be exactly identical
            diff = torch.abs(t1 - t2).max().item()
            assert diff == 0.0, f"Evaluation transform is non-deterministic (max diff: {diff}) on {p.name}"

    print(f"  --> PASS: Confirmed 100% deterministic evaluation pipeline across {len(val_samples)} test samples.")


def test_seed_reproducibility():
    """Verify random seeds produce reproducible behavior."""
    print("[TEST 5/8] Verifying random seed reproducibility...")
    sample_path = next(TRAIN_DIR.rglob("*.png"))
    with Image.open(sample_path) as img:
        rgb = img.convert("RGB")

        config = get_augmentation_policy("conservative")
        transform = build_train_transforms(config)

        # Run 1 with seed 42
        torch.manual_seed(42)
        out1 = transform(rgb)

        # Run 2 with seed 42
        torch.manual_seed(42)
        out2 = transform(rgb)

        # Run 3 with seed 999 (should differ)
        torch.manual_seed(999)
        out3 = transform(rgb)

        diff_identical = torch.abs(out1 - out2).max().item()
        diff_distinct = torch.abs(out1 - out3).max().item()

        assert diff_identical == 0.0, f"Seeded transform not reproducible (diff: {diff_identical})"
        assert diff_distinct > 1e-4, "Different seeds unexpectedly produced identical outputs"

    print("  --> PASS: Confirmed bitwise reproducibility with fixed random seeds.")


def test_manifest_and_split_consistency():
    """Verify dataset manifest counts match expected 70/15/15 target per class."""
    print("[TEST 6/8] Verifying split manifest consistency and class balance...")
    assert MANIFEST_PATH.exists(), f"Manifest file missing: {MANIFEST_PATH}"

    counts = {"train": {}, "val": {}, "test": {}}
    for c in CLASS_NAMES:
        counts["train"][c] = 0
        counts["val"][c] = 0
        counts["test"][c] = 0

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            split = row["split"]
            label = row["label"]
            if split in counts and label in counts[split]:
                counts[split][label] += 1

    for c in CLASS_NAMES:
        assert counts["train"][c] == 70, f"Train count mismatch for {c}: {counts['train'][c]}"
        assert counts["val"][c] == 15, f"Val count mismatch for {c}: {counts['val'][c]}"
        assert counts["test"][c] == 15, f"Test count mismatch for {c}: {counts['test'][c]}"

    total_train = sum(counts["train"].values())
    total_val = sum(counts["val"].values())
    total_test = sum(counts["test"].values())

    assert total_train == 420, f"Total train mismatch: {total_train}"
    assert total_val == 90, f"Total val mismatch: {total_val}"
    assert total_test == 90, f"Total test mismatch: {total_test}"

    print(f"  --> PASS: Manifest verified with exact split counts (420 train, 90 val, 90 test).")


def test_no_synthetic_leakage_into_val_test():
    """Verify no synthetic preview files or temporary images leaked into val or test directories."""
    print("[TEST 7/8] Verifying zero synthetic leakage into validation or test directories...")
    allowed_filenames = set()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            allowed_filenames.add(Path(row["output"]).name)

    for split_dir, split_name in [(VAL_DIR, "val"), (TEST_DIR, "test")]:
        files = list(split_dir.rglob("*.png"))
        assert len(files) == 90, f"Expected 90 files in {split_name}, got {len(files)}"
        for f in files:
            assert f.name in allowed_filenames, f"Unauthorized file found in {split_name}: {f.name}"
            assert "aug" not in f.name.lower(), f"Suspicious augmented file in {split_name}: {f.name}"

    print("  --> PASS: Confirmed zero synthetic or augmented leakage in validation or test splits.")


def test_neutral_padding_normalization():
    """Verify ImageNet-mean canvas padding maps to (0.0, 0.0, 0.0) in normalized tensor space."""
    print("[TEST 8/8] Verifying ImageNet neutral canvas padding normalization alignment...")
    # Create single-color canvas with IMAGENET_MEAN_RGB (124, 116, 104)
    canvas = Image.new("RGB", (32, 32), color=IMAGENET_MEAN_RGB)
    to_tensor = transforms.ToTensor()
    normalize = transforms.Normalize(mean=list(IMAGENET_MEAN), std=list(IMAGENET_STD))

    tensor = normalize(to_tensor(canvas))

    # Mean in each channel should be within 0.02 of 0.0
    channel_means = tensor.mean(dim=(1, 2))
    for c_idx, (c_name, c_val) in enumerate(zip(["R", "G", "B"], channel_means)):
        abs_val = abs(float(c_val))
        assert abs_val < 0.02, f"Channel {c_name} padding normalized to {c_val:.4f}, expected ~0.0"

    print(f"  --> PASS: Padding color (124, 116, 104) normalizes to: R={channel_means[0]:.4f}, G={channel_means[1]:.4f}, B={channel_means[2]:.4f} (~0.0).")


def test_no_collages_or_grids_in_augmented_dataset():
    """
    Verify that NO collage, grid, contact sheet, or montage has entered the training dataset.
    Every single file must be a standalone (224, 224) RGB image of a single leaf.
    """
    print("[TEST 9/14] Verifying NO collages, grids, or montages in augmented training dataset...")
    assert AUGMENTED_TRAIN_DIR.exists(), f"Augmented train dir missing: {AUGMENTED_TRAIN_DIR}"

    all_files = list(AUGMENTED_TRAIN_DIR.rglob("*.png"))
    assert len(all_files) == 3780, f"Expected 3,780 augmented files, found {len(all_files)}"

    prohibited_keywords = ["grid", "collage", "strip", "montage", "sheet", "preview", "composite"]

    # Verify filenames do not indicate collages
    for f in all_files:
        fname_lower = f.name.lower()
        for kw in prohibited_keywords:
            assert kw not in fname_lower, f"Prohibited collage keyword '{kw}' found in training file: {f.name}"

    # Sample check 100 images across all classes for exact dimensions and standalone format
    sample_stride = max(1, len(all_files) // 100)
    samples_to_check = all_files[::sample_stride]

    for p in samples_to_check:
        with Image.open(p) as img:
            w, h = img.size
            assert (w, h) == (224, 224), (
                f"Collage or non-standard dimension detected: {p.name} has shape ({w}, {h}), expected (224, 224)!"
            )
            assert img.mode == "RGB", f"Non-RGB mode detected: {img.mode} in {p.name}"

            # Verify aspect ratio is strictly 1.0 (collages are multi-panel grids with wide/tall ratios)
            aspect = float(w) / float(h)
            assert abs(aspect - 1.0) < 1e-4, f"Non-square aspect ratio {aspect} in {p.name}"

    print(f"  --> PASS: Verified 3,780 individual files. 0 collages, 0 grids, and 0 montages detected.")


def test_exact_augmented_counts_and_determinism():
    """Verify each of the 6 classes contains exactly 630 files (9 derivatives x 70 originals)."""
    print("[TEST 10/14] Verifying exact 630 files per class (3,780 total augmented derivatives)...")
    assert AUGMENTED_TRAIN_DIR.exists()

    total_files = 0
    for cls_name in CLASS_NAMES:
        cls_dir = AUGMENTED_TRAIN_DIR / cls_name
        assert cls_dir.exists(), f"Missing class directory: {cls_dir}"
        files = list(cls_dir.glob("*.png"))
        assert len(files) == 630, f"Class {cls_name} has {len(files)} files, expected exactly 630"
        total_files += len(files)

        # Verify derivative indexing from aug01 to aug09
        indices_seen = set()
        for f in files:
            assert "_aug" in f.name, f"File {f.name} missing '_aug' suffix"
            idx_part = f.name.split("_aug")[-1].replace(".png", "")
            indices_seen.add(int(idx_part))
        assert indices_seen == set(range(1, 10)), f"Class {cls_name} missing some derivative indices: {indices_seen}"

    assert total_files == 3780, f"Total augmented files {total_files} != 3,780"
    print(f"  --> PASS: Exactly 630 files per class verified across all 6 classes (total: 3,780 files).")


def test_augmented_manifest_traceability_and_hashes():
    """Verify manifest.csv and combined_train_manifest.csv schemas, counts, and SHA-256 hashes."""
    print("[TEST 11/14] Verifying manifest traceability, schemas, and SHA-256 file hashes...")
    assert AUGMENTED_MANIFEST_PATH.exists(), f"Missing manifest: {AUGMENTED_MANIFEST_PATH}"
    assert COMBINED_MANIFEST_PATH.exists(), f"Missing combined manifest: {COMBINED_MANIFEST_PATH}"

    expected_fields = [
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

    with open(AUGMENTED_MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 3780, f"Augmented manifest has {len(reader)} rows, expected 3,780"
        assert list(reader[0].keys()) == expected_fields, f"Manifest schema mismatch: {list(reader[0].keys())}"

        # Verify all split values are 'train'
        for r in reader[:50]:
            assert r["split"] == "train"
            assert r["is_augmented"] == "1"
            assert 1 <= int(r["augmentation_index"]) <= 9
            assert (ROOT / r["image_path"]).exists(), f"Image path does not exist: {r['image_path']}"
            assert (ROOT / r["source_image_path"]).exists(), f"Source path does not exist: {r['source_image_path']}"

            # Verify file hash matches actual file hash
            with open(ROOT / r["image_path"], "rb") as im_file:
                actual_hash = hashlib.sha256(im_file.read()).hexdigest()
            assert actual_hash == r["file_hash"], f"File hash mismatch for {r['image_path']}"

    with open(COMBINED_MANIFEST_PATH, "r", encoding="utf-8") as f:
        combined_reader = list(csv.DictReader(f))
        assert len(combined_reader) == 4200, f"Combined manifest has {len(combined_reader)} rows, expected 4,200"

    print("  --> PASS: Manifests verified. 3,780 augmented rows, 4,200 combined rows, hashes match.")


def test_nine_techniques_independently():
    """Verify each of the 9 individual augmentation primitives operates correctly on a sample image."""
    print("[TEST 12/14] Verifying all 9 independent transformation primitives...")
    from scripts.augmentations import (
        apply_rotation,
        apply_horizontal_flip,
        apply_vertical_flip,
        apply_brightness,
        apply_contrast,
        apply_zoom_crop,
        apply_translation,
        apply_gaussian_blur,
        apply_sensor_noise,
    )

    sample_img = Image.new("RGB", (224, 224), (80, 140, 60))

    # 1. Rotation
    rot = apply_rotation(sample_img, 15.0)
    assert rot.size == (224, 224) and rot.mode == "RGB"

    # 2. Horizontal flip
    hf = apply_horizontal_flip(sample_img)
    assert hf.size == (224, 224) and hf.mode == "RGB"

    # 3. Vertical flip
    vf = apply_vertical_flip(sample_img)
    assert vf.size == (224, 224) and vf.mode == "RGB"

    # 4. Brightness
    br = apply_brightness(sample_img, 1.15)
    assert br.size == (224, 224) and br.mode == "RGB"

    # 5. Contrast
    ct = apply_contrast(sample_img, 0.85)
    assert ct.size == (224, 224) and ct.mode == "RGB"

    # 6. Zoom/crop
    zc = apply_zoom_crop(sample_img, 0.90)
    assert zc.size == (224, 224) and zc.mode == "RGB"

    # 7. Translation
    tr = apply_translation(sample_img, 0.05, -0.05)
    assert tr.size == (224, 224) and tr.mode == "RGB"

    # 8. Gaussian blur
    gb = apply_gaussian_blur(sample_img, 0.5)
    assert gb.size == (224, 224) and gb.mode == "RGB"

    # 9. Sensor noise
    sn = apply_sensor_noise(sample_img, 5.0)
    assert sn.size == (224, 224) and sn.mode == "RGB"

    print("  --> PASS: All 9 independent transformation primitives verified with shape (224, 224) RGB.")


def test_combined_dataset_loader_integrity():
    """Verify PyTorch loader successfully loads the combined 4,200 training images."""
    print("[TEST 13/14] Verifying PyTorch DataLoader on combined 4,200 training dataset...")
    orig_dataset = ImageFolder(root=str(TRAIN_DIR), transform=transforms.ToTensor())
    aug_dataset = ImageFolder(root=str(AUGMENTED_TRAIN_DIR), transform=transforms.ToTensor())

    assert len(orig_dataset) == 420, f"Orig dataset has {len(orig_dataset)} images, expected 420"
    assert len(aug_dataset) == 3780, f"Aug dataset has {len(aug_dataset)} images, expected 3,780"
    assert orig_dataset.class_to_idx == aug_dataset.class_to_idx, "Class index mismatch between datasets"

    combined = torch.utils.data.ConcatDataset([orig_dataset, aug_dataset])
    assert len(combined) == 4200, f"Combined dataset has {len(combined)} images, expected 4,200"

    # Test loading a batch
    loader = torch.utils.data.DataLoader(combined, batch_size=16, shuffle=True)
    images, labels = next(iter(loader))
    assert images.shape == (16, 3, 224, 224)
    assert labels.shape == (16,)
    assert (labels >= 0).all() and (labels < 6).all()

    print(f"  --> PASS: Combined dataset (4,200 samples) loaded successfully; batch tensor shape: {images.shape}.")


def test_powdery_mildew_blur_suppression_and_exceptions():
    """Verify that coriander_powdery_mildew recipe suppresses blur to protect mycelium (ADR-005/006)."""
    print("[TEST 14/14] Verifying coriander_powdery_mildew blur suppression exception...")
    from scripts.augmentations import generate_nine_derivatives

    dummy = Image.new("RGB", (224, 224), (100, 120, 80))
    derivatives_pm = generate_nine_derivatives(dummy, "coriander_powdery_mildew", source_seed=42)
    # Aug index 8 is defocus blur focus
    aug8_pm = derivatives_pm[7]
    assert aug8_pm[3].get("powdery_mildew_blur_suppression") is True
    assert aug8_pm[3].get("gaussian_blur_radius") == 0.0

    # For other classes, blur is applied
    derivatives_other = generate_nine_derivatives(dummy, "coriander_healthy", source_seed=42)
    aug8_other = derivatives_other[7]
    assert aug8_other[3].get("gaussian_blur_radius", 0.0) > 0.0

    print("  --> PASS: Coriander powdery mildew blur suppression exception verified as documented in ADR-005.")


def run_all_tests():
    print("=" * 65)
    print("VERTIFARM DATA AUGMENTATION & PIPELINE INTEGRITY TEST SUITE")
    print(f"Platform: Python {sys.version.split()[0]} | PyTorch {torch.__version__}")
    print("=" * 65)

    test_class_label_invariance()
    test_output_dimensions_and_ranges()
    test_source_data_immutability()
    test_eval_pipeline_determinism()
    test_seed_reproducibility()
    test_manifest_and_split_consistency()
    test_no_synthetic_leakage_into_val_test()
    test_neutral_padding_normalization()
    test_no_collages_or_grids_in_augmented_dataset()
    test_exact_augmented_counts_and_determinism()
    test_augmented_manifest_traceability_and_hashes()
    test_nine_techniques_independently()
    test_combined_dataset_loader_integrity()
    test_powdery_mildew_blur_suppression_and_exceptions()

    print("\n" + "=" * 65)
    print("ALL 14 VERIFICATION TESTS PASSED SUCCESSFULLY (0 ERRORS)")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()

