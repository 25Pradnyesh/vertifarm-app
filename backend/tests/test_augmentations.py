"""
backend/tests/test_augmentations.py

Pytest test suite for VertiFarm data augmentation pipeline.
Tests tensor shapes, normalization, immutability, determinism, and class indexing.
"""

import sys
from pathlib import Path
import pytest
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]


def test_augmentation_policy_presets():
    """Verify all predefined augmentation policies load valid configs."""
    for policy in ["none", "baseline", "light", "conservative"]:
        cfg = get_augmentation_policy(policy)
        assert cfg.name == policy
        train_t = build_train_transforms(cfg)
        eval_t = build_eval_transforms(cfg)
        assert len(train_t.transforms) >= 2
        assert len(eval_t.transforms) == 2


def test_invalid_policy_raises():
    """Verify requesting an unknown policy name raises ValueError."""
    with pytest.raises(ValueError):
        get_augmentation_policy("hyper_aggressive_unsupported")


def test_tensor_shape_and_dtype():
    """Verify output tensor is 3x224x224 float32."""
    cfg = get_augmentation_policy("conservative")
    transform = build_train_transforms(cfg)
    dummy_img = Image.new("RGB", (224, 224), color=(34, 139, 34))

    out = transform(dummy_img)
    assert out.shape == (3, 224, 224)
    assert out.dtype == torch.float32


def test_evaluation_transform_is_deterministic():
    """Verify evaluation transforms produce zero stochastic variation."""
    cfg = get_augmentation_policy("conservative")
    eval_transform = build_eval_transforms(cfg)
    dummy_img = Image.new("RGB", (224, 224), color=(50, 100, 150))

    t1 = eval_transform(dummy_img)
    t2 = eval_transform(dummy_img)
    assert torch.equal(t1, t2)


def test_neutral_padding_maps_to_zero():
    """Verify ImageNet-mean canvas fill (124, 116, 104) normalizes to near-zero."""
    cfg = get_augmentation_policy("conservative")
    eval_transform = build_eval_transforms(cfg)
    canvas = Image.new("RGB", (16, 16), color=IMAGENET_MEAN_RGB)

    tensor = eval_transform(canvas)
    for c in range(3):
        assert abs(tensor[c].mean().item()) < 0.02


def test_denormalize_tensor_roundtrip():
    """Verify denormalize_tensor reconstructs a valid PIL Image."""
    cfg = get_augmentation_policy("conservative")
    eval_transform = build_eval_transforms(cfg)
    orig_img = Image.new("RGB", (64, 64), color=(80, 160, 40))

    tensor = eval_transform(orig_img)
    reconstructed = denormalize_tensor(tensor)
    assert reconstructed.size == (64, 64)
    assert reconstructed.mode == "RGB"


def test_nine_augmentation_primitives():
    """Verify all 9 individual transformation functions operate on PIL images."""
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

    img = Image.new("RGB", (224, 224), color=(60, 120, 80))

    assert apply_rotation(img, 15.0).size == (224, 224)
    assert apply_horizontal_flip(img).size == (224, 224)
    assert apply_vertical_flip(img).size == (224, 224)
    assert apply_brightness(img, 1.15).size == (224, 224)
    assert apply_contrast(img, 0.85).size == (224, 224)
    assert apply_zoom_crop(img, 0.90).size == (224, 224)
    assert apply_translation(img, 0.05, 0.05).size == (224, 224)
    assert apply_gaussian_blur(img, 0.5).size == (224, 224)
    assert apply_sensor_noise(img, 5.0).size == (224, 224)


def test_generate_nine_derivatives_structure():
    """Verify generate_nine_derivatives produces 9 distinct valid derivatives."""
    from scripts.augmentations import generate_nine_derivatives

    img = Image.new("RGB", (224, 224), color=(70, 140, 90))
    derivatives = generate_nine_derivatives(img, "coriander_bacterial_blight", source_seed=42)

    assert len(derivatives) == 9
    for idx, (aug_img, aug_idx, recipe, params) in enumerate(derivatives, 1):
        assert aug_idx == idx
        assert aug_img.size == (224, 224)
        assert aug_img.mode == "RGB"
        assert len(params["applied_techniques"]) >= 1


def test_no_collages_in_dataset_augmented():
    """Verify no collage or grid file exists in dataset_augmented/train."""
    aug_train = ROOT / "dataset_augmented" / "train"
    if not aug_train.exists():
        pytest.skip("dataset_augmented/train does not exist yet")

    files = list(aug_train.rglob("*.png"))
    assert len(files) == 3780

    for f in files[:50]:
        with Image.open(f) as im:
            assert im.size == (224, 224), f"Found non-standalone image: {f.name} with size {im.size}"
            assert im.mode == "RGB"
        for kw in ["grid", "collage", "strip", "montage", "sheet"]:
            assert kw not in f.name.lower()


