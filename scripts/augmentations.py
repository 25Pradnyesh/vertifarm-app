#!/usr/bin/env python3
"""
scripts/augmentations.py

VertiFarm Agronomically-Safe Data Augmentation Pipeline.

Key Design Principles:
1. Phytopathological Feature Preservation:
   - Strict hue limitation (<= 0.01) to avoid altering chlorosis (yellowing), necrosis (browning),
     or fungal mycelium (white powder) signatures.
   - Conservative crop scaling (>= 0.88) so localized disease lesions are never excised.
2. Boundary Neutrality:
   - Spatial rotations and affine translations use ImageNet-mean canvas fill (124, 116, 104).
   - In normalized tensor space, this maps to (0.0, 0.0, 0.0), eliminating artificial border edge artifacts.
3. Strict Partition Isolation:
   - Stochastic transformations apply strictly to training data on-the-fly.
   - Validation and test sets receive only deterministic evaluation preprocessing (ToTensor + Normalize).
4. Full Parameter Transparency & Configurability:
   - Dataclass-based policy architecture supporting 'none', 'baseline', 'conservative', and 'light'.
"""

from dataclasses import dataclass, field
import json
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import torch
import torchvision.transforms as transforms

# ImageNet standard normalization constants
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# ImageNet RGB mean in uint8: [0.485*255=124, 0.456*255=116, 0.406*255=104]
IMAGENET_MEAN_RGB = (124, 116, 104)


# =============================================================================
# 9 INDEPENDENT AUGMENTATION PRIMITIVES (PIL / NUMPY)
# =============================================================================

def apply_rotation(
    img: Image.Image,
    degrees: float,
    fill_color: Tuple[int, int, int] = IMAGENET_MEAN_RGB,
) -> Image.Image:
    """Technique 1: Rotation within +/- 20 degrees with ImageNet-mean canvas fill."""
    if abs(degrees) < 1e-3:
        return img
    return img.rotate(degrees, resample=Image.Resampling.BILINEAR, fillcolor=fill_color)


def apply_horizontal_flip(img: Image.Image) -> Image.Image:
    """Technique 2: Horizontal flip (left-right reflection)."""
    return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def apply_vertical_flip(img: Image.Image) -> Image.Image:
    """Technique 3: Vertical flip (top-bottom reflection for top-down canopy)."""
    return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def apply_brightness(img: Image.Image, factor: float) -> Image.Image:
    """Technique 4: Photometric brightness adjustment (factor in ~0.80 to 1.20)."""
    if abs(factor - 1.0) < 1e-3:
        return img
    return ImageEnhance.Brightness(img).enhance(factor)


def apply_contrast(img: Image.Image, factor: float) -> Image.Image:
    """Technique 5: Photometric contrast adjustment (factor in ~0.80 to 1.20)."""
    if abs(factor - 1.0) < 1e-3:
        return img
    return ImageEnhance.Contrast(img).enhance(factor)


def apply_zoom_crop(
    img: Image.Image,
    scale_factor: float,
    fill_color: Tuple[int, int, int] = IMAGENET_MEAN_RGB,
) -> Image.Image:
    """
    Technique 6: Zoom / crop up to 15% (scale_factor in [0.85, 1.0]).
    Preserves diagnostic lesions by retaining at least 85% of dimensions.
    """
    if scale_factor >= 0.999:
        return img
    w, h = img.size
    crop_w = max(16, int(round(w * scale_factor)))
    crop_h = max(16, int(round(h * scale_factor)))
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    cropped = img.crop((left, top, left + crop_w, top + crop_h))
    return cropped.resize((w, h), Image.Resampling.BILINEAR)


def apply_translation(
    img: Image.Image,
    dx_percent: float,
    dy_percent: float,
    fill_color: Tuple[int, int, int] = IMAGENET_MEAN_RGB,
) -> Image.Image:
    """
    Technique 7: Translation up to +/- 10% of image dimensions with ImageNet-mean canvas fill.
    """
    if abs(dx_percent) < 1e-4 and abs(dy_percent) < 1e-4:
        return img
    w, h = img.size
    dx_px = int(round(w * dx_percent))
    dy_px = int(round(h * dy_percent))
    matrix = (1, 0, -dx_px, 0, 1, -dy_px)
    return img.transform(
        (w, h),
        Image.Transform.AFFINE,
        matrix,
        fillcolor=fill_color,
        resample=Image.Resampling.BILINEAR,
    )


def apply_gaussian_blur(img: Image.Image, radius: float) -> Image.Image:
    """Technique 8: Mild Gaussian defocus blur (radius in [0.2, 0.7])."""
    if radius <= 1e-3:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_sensor_noise(
    img: Image.Image,
    noise_std: float,
    rng: Optional[np.random.RandomState] = None,
) -> Image.Image:
    """
    Technique 9: Mild additive Gaussian sensor noise (noise_std in [2.0, 7.0] in 0-255 scale).
    Simulates camera sensor gain and low-cost sensor grain.
    """
    if noise_std <= 1e-3:
        return img
    arr = np.array(img, dtype=np.float32)
    if rng is None:
        noise = np.random.normal(0.0, noise_std, arr.shape)
    else:
        noise = rng.normal(0.0, noise_std, arr.shape)
    noisy_arr = np.clip(arr + noise, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(noisy_arr)


# =============================================================================
# DETERMINISTIC 9-DERIVATIVE GENERATION PIPELINE
# =============================================================================

def generate_nine_derivatives(
    image: Image.Image,
    class_name: str,
    source_seed: int,
    fill_color: Tuple[int, int, int] = IMAGENET_MEAN_RGB,
) -> List[Tuple[Image.Image, int, str, Dict[str, Any]]]:
    """
    Generates exactly 9 separately transformed derivative images from one source image.
    
    Each derivative focuses on distinct augmentation techniques while strictly preserving:
    - Diagnostic disease lesion features and color integrity.
    - Class label correctness.
    - Deterministic reproducibility given source_seed.
    - Standalone single-image format (224x224 RGB).
    
    Returns:
        List of tuples: (augmented_pil_image, aug_index_1_to_9, recipe_name, parameter_dict)
    """
    derivatives = []
    
    for aug_idx in range(1, 10):
        # Create deterministic pseudo-random state per derivative
        d_seed = (source_seed * 31 + aug_idx * 10007) & 0x7FFFFFFF
        rng_py = random.Random(d_seed)
        rng_np = np.random.RandomState(d_seed)
        
        cur = image.copy()
        params: Dict[str, Any] = {
            "rotation_deg": 0.0,
            "hflip": False,
            "vflip": False,
            "brightness_factor": 1.0,
            "contrast_factor": 1.0,
            "zoom_crop_scale": 1.0,
            "translation_pct": [0.0, 0.0],
            "gaussian_blur_radius": 0.0,
            "sensor_noise_std": 0.0,
            "applied_techniques": [],
        }
        
        recipe_name = f"recipe_{aug_idx:02d}"
        
        if aug_idx == 1:
            # 1. Rotation emphasis (+/- 12 to 20 deg) + occasional horizontal flip
            recipe_name = "rotation_focus"
            sign = rng_py.choice([-1.0, 1.0])
            deg = sign * rng_py.uniform(12.0, 19.5)
            cur = apply_rotation(cur, deg, fill_color)
            params["rotation_deg"] = round(deg, 2)
            params["applied_techniques"].append("rotation")
            if rng_py.random() < 0.5:
                cur = apply_horizontal_flip(cur)
                params["hflip"] = True
                params["applied_techniques"].append("horizontal_flip")

        elif aug_idx == 2:
            # 2. Horizontal Flip & Lateral Symmetry + mild rotation
            recipe_name = "hflip_orientation"
            cur = apply_horizontal_flip(cur)
            params["hflip"] = True
            params["applied_techniques"].append("horizontal_flip")
            deg = rng_py.uniform(-8.0, 8.0)
            cur = apply_rotation(cur, deg, fill_color)
            params["rotation_deg"] = round(deg, 2)
            params["applied_techniques"].append("rotation")

        elif aug_idx == 3:
            # 3. Brightness Photometric Variation (+/- 15% to 18%)
            recipe_name = "brightness_exposure"
            # Sample either dark or bright
            factor = rng_py.choice([rng_py.uniform(0.82, 0.86), rng_py.uniform(1.14, 1.18)])
            cur = apply_brightness(cur, factor)
            params["brightness_factor"] = round(factor, 3)
            params["applied_techniques"].append("brightness")
            # Mild contrast adjustment
            cfactor = rng_py.uniform(0.95, 1.05)
            cur = apply_contrast(cur, cfactor)
            params["contrast_factor"] = round(cfactor, 3)

        elif aug_idx == 4:
            # 4. Contrast Photometric Variation (+/- 15% to 18%)
            recipe_name = "contrast_illumination"
            cfactor = rng_py.choice([rng_py.uniform(0.82, 0.86), rng_py.uniform(1.14, 1.18)])
            cur = apply_contrast(cur, cfactor)
            params["contrast_factor"] = round(cfactor, 3)
            params["applied_techniques"].append("contrast")
            # Mild brightness adjustment
            bfactor = rng_py.uniform(0.95, 1.05)
            cur = apply_brightness(cur, bfactor)
            params["brightness_factor"] = round(bfactor, 3)

        elif aug_idx == 5:
            # 5. Zoom / Crop (scale 0.88 to 0.94, up to 12% crop)
            recipe_name = "zoom_crop_focus"
            scale = rng_py.uniform(0.88, 0.94)
            cur = apply_zoom_crop(cur, scale, fill_color)
            params["zoom_crop_scale"] = round(scale, 3)
            params["applied_techniques"].append("zoom_crop")
            if rng_py.random() < 0.5:
                cur = apply_horizontal_flip(cur)
                params["hflip"] = True
                params["applied_techniques"].append("horizontal_flip")

        elif aug_idx == 6:
            # 6. Spatial Translation (shift 4% to 8% in X and Y)
            recipe_name = "translation_framing"
            dx = rng_py.choice([-1.0, 1.0]) * rng_py.uniform(0.04, 0.08)
            dy = rng_py.choice([-1.0, 1.0]) * rng_py.uniform(0.04, 0.08)
            cur = apply_translation(cur, dx, dy, fill_color)
            params["translation_pct"] = [round(dx, 3), round(dy, 3)]
            params["applied_techniques"].append("translation")
            deg = rng_py.uniform(-5.0, 5.0)
            cur = apply_rotation(cur, deg, fill_color)
            params["rotation_deg"] = round(deg, 2)
            params["applied_techniques"].append("rotation")

        elif aug_idx == 7:
            # 7. Camera Sensor Noise (mild Gaussian noise std 3.5 to 6.5)
            recipe_name = "sensor_noise_gain"
            noise_std = rng_py.uniform(3.5, 6.5)
            cur = apply_sensor_noise(cur, noise_std, rng_np)
            params["sensor_noise_std"] = round(noise_std, 2)
            params["applied_techniques"].append("sensor_noise")
            if rng_py.random() < 0.5:
                cur = apply_horizontal_flip(cur)
                params["hflip"] = True
                params["applied_techniques"].append("horizontal_flip")

        elif aug_idx == 8:
            # 8. Gaussian Defocus Blur (with scientific powdery mildew protection)
            recipe_name = "defocus_blur_focus"
            if class_name == "coriander_powdery_mildew":
                # ADR-005/ADR-006: Blur attenuates fine mycelial hyphae; replace with mild translation & scale
                scale = rng_py.uniform(0.92, 0.97)
                cur = apply_zoom_crop(cur, scale, fill_color)
                params["zoom_crop_scale"] = round(scale, 3)
                params["applied_techniques"].append("zoom_crop")
                deg = rng_py.uniform(-6.0, 6.0)
                cur = apply_rotation(cur, deg, fill_color)
                params["rotation_deg"] = round(deg, 2)
                params["applied_techniques"].append("rotation")
                params["powdery_mildew_blur_suppression"] = True
            else:
                radius = rng_py.uniform(0.35, 0.65)
                cur = apply_gaussian_blur(cur, radius)
                params["gaussian_blur_radius"] = round(radius, 3)
                params["applied_techniques"].append("gaussian_blur")

        elif aug_idx == 9:
            # 9. Controlled Multi-Technique Composite (mild rotation, vertical flip if realistic, mild jitter)
            recipe_name = "multi_technique_composite"
            # Vertical flip (simulating top-down overhead capture)
            if rng_py.random() < 0.4:
                cur = apply_vertical_flip(cur)
                params["vflip"] = True
                params["applied_techniques"].append("vertical_flip")
            if rng_py.random() < 0.5:
                cur = apply_horizontal_flip(cur)
                params["hflip"] = True
                params["applied_techniques"].append("horizontal_flip")
            deg = rng_py.uniform(-10.0, 10.0)
            cur = apply_rotation(cur, deg, fill_color)
            params["rotation_deg"] = round(deg, 2)
            params["applied_techniques"].append("rotation")
            bfactor = rng_py.uniform(0.92, 1.08)
            cur = apply_brightness(cur, bfactor)
            params["brightness_factor"] = round(bfactor, 3)
            dx = rng_py.uniform(-0.03, 0.03)
            dy = rng_py.uniform(-0.03, 0.03)
            cur = apply_translation(cur, dx, dy, fill_color)
            params["translation_pct"] = [round(dx, 3), round(dy, 3)]
            params["applied_techniques"].append("translation")

        assert cur.size == (224, 224), f"Generated derivative #{aug_idx} has invalid size: {cur.size}"
        assert cur.mode == "RGB", f"Generated derivative #{aug_idx} has invalid mode: {cur.mode}"
        derivatives.append((cur, aug_idx, recipe_name, params))
        
    return derivatives


@dataclass
class AugmentationConfig:
    """Configurable parameters for plant disease image augmentation."""

    name: str = "conservative"

    # Geometric transformations
    horizontal_flip_prob: float = 0.5
    vertical_flip_prob: float = 0.2  # Top-down views permit mild vertical flip; side views preserve gravity
    rotation_degrees: float = 20.0
    translate_percent: Tuple[float, float] = (0.04, 0.04)  # Max 4% shift in X and Y
    scale_range: Tuple[float, float] = (0.95, 1.05)  # Mild camera distance variation

    # Cropping
    enable_random_crop: bool = True
    crop_scale: Tuple[float, float] = (0.88, 1.0)  # Conservative: never crop out small lesion spots
    crop_ratio: Tuple[float, float] = (0.92, 1.08)  # Near-square aspect ratio preserved

    # Photometric adjustments (strictly conservative hue)
    brightness_jitter: float = 0.15
    contrast_jitter: float = 0.15
    saturation_jitter: float = 0.10
    hue_jitter: float = 0.01  # STRICT: >0.02 corrupts chlorotic/necrotic diagnostic boundaries

    # Optical sensor / defocus noise
    enable_blur: bool = True
    blur_prob: float = 0.20
    blur_kernel_size: int = 3
    blur_sigma: Tuple[float, float] = (0.1, 0.8)

    # Canvas & normalization
    target_size: int = 224
    padding_color: Tuple[int, int, int] = IMAGENET_MEAN_RGB
    mean: Tuple[float, float, float] = IMAGENET_MEAN
    std: Tuple[float, float, float] = IMAGENET_STD


def get_augmentation_policy(policy_name: str = "conservative") -> AugmentationConfig:
    """Returns preset AugmentationConfig by policy name."""
    cleaned = policy_name.strip().lower()

    if cleaned == "none":
        return AugmentationConfig(
            name="none",
            horizontal_flip_prob=0.0,
            vertical_flip_prob=0.0,
            rotation_degrees=0.0,
            translate_percent=(0.0, 0.0),
            scale_range=(1.0, 1.0),
            enable_random_crop=False,
            brightness_jitter=0.0,
            contrast_jitter=0.0,
            saturation_jitter=0.0,
            hue_jitter=0.0,
            enable_blur=False,
        )

    elif cleaned == "baseline":
        return AugmentationConfig(
            name="baseline",
            horizontal_flip_prob=0.5,
            vertical_flip_prob=0.5,
            rotation_degrees=15.0,
            translate_percent=(0.0, 0.0),
            scale_range=(1.0, 1.0),
            enable_random_crop=False,
            brightness_jitter=0.1,
            contrast_jitter=0.1,
            saturation_jitter=0.1,
            hue_jitter=0.0,
            enable_blur=False,
        )

    elif cleaned == "light":
        return AugmentationConfig(
            name="light",
            horizontal_flip_prob=0.5,
            vertical_flip_prob=0.0,
            rotation_degrees=10.0,
            translate_percent=(0.02, 0.02),
            scale_range=(0.98, 1.02),
            enable_random_crop=False,
            brightness_jitter=0.10,
            contrast_jitter=0.10,
            saturation_jitter=0.05,
            hue_jitter=0.0,
            enable_blur=False,
        )

    elif cleaned == "conservative":
        return AugmentationConfig(name="conservative")

    else:
        raise ValueError(
            f"Unknown augmentation policy: '{policy_name}'. Valid options: ['none', 'baseline', 'light', 'conservative']"
        )


def build_train_transforms(config: Optional[AugmentationConfig] = None) -> transforms.Compose:
    """
    Constructs the stochastic data augmentation pipeline for training.
    Executes on-the-fly during training data loading.
    """
    if config is None:
        config = AugmentationConfig()

    ops = []

    # 1. Conservative random crop (zoom) if enabled
    if config.enable_random_crop and config.crop_scale[0] < 1.0:
        ops.append(
            transforms.RandomResizedCrop(
                size=(config.target_size, config.target_size),
                scale=config.crop_scale,
                ratio=config.crop_ratio,
                interpolation=transforms.InterpolationMode.BILINEAR,
            )
        )

    # 2. Horizontal flipping
    if config.horizontal_flip_prob > 0.0:
        ops.append(transforms.RandomHorizontalFlip(p=config.horizontal_flip_prob))

    # 3. Vertical flipping (conservative)
    if config.vertical_flip_prob > 0.0:
        ops.append(transforms.RandomVerticalFlip(p=config.vertical_flip_prob))

    # 4. Rotation with ImageNet-mean canvas fill
    if config.rotation_degrees > 0.0:
        ops.append(
            transforms.RandomRotation(
                degrees=(-config.rotation_degrees, config.rotation_degrees),
                fill=config.padding_color,
                interpolation=transforms.InterpolationMode.BILINEAR,
            )
        )

    # 5. Mild affine translation and scale zoom with ImageNet-mean canvas fill
    if (
        config.translate_percent != (0.0, 0.0)
        or config.scale_range != (1.0, 1.0)
    ):
        ops.append(
            transforms.RandomAffine(
                degrees=0,
                translate=config.translate_percent,
                scale=config.scale_range,
                fill=config.padding_color,
                interpolation=transforms.InterpolationMode.BILINEAR,
            )
        )

    # 6. Photometric color jitter (strictly restricted hue)
    if (
        config.brightness_jitter > 0.0
        or config.contrast_jitter > 0.0
        or config.saturation_jitter > 0.0
        or config.hue_jitter > 0.0
    ):
        ops.append(
            transforms.ColorJitter(
                brightness=config.brightness_jitter,
                contrast=config.contrast_jitter,
                saturation=config.saturation_jitter,
                hue=config.hue_jitter,
            )
        )

    # 7. Mild camera defocus blur simulation
    if config.enable_blur and config.blur_prob > 0.0:
        ops.append(
            transforms.RandomApply(
                [
                    transforms.GaussianBlur(
                        kernel_size=config.blur_kernel_size,
                        sigma=config.blur_sigma,
                    )
                ],
                p=config.blur_prob,
            )
        )

    # 8. Conversion to tensor and ImageNet normalization
    ops.append(transforms.ToTensor())
    ops.append(transforms.Normalize(mean=list(config.mean), std=list(config.std)))

    return transforms.Compose(ops)


def build_eval_transforms(config: Optional[AugmentationConfig] = None) -> transforms.Compose:
    """
    Constructs deterministic preprocessing pipeline for validation and test splits.
    Strictly NO stochastic augmentation.
    """
    if config is None:
        config = AugmentationConfig()

    return transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=list(config.mean), std=list(config.std)),
    ])


def denormalize_tensor(
    tensor: torch.Tensor,
    mean: Tuple[float, float, float] = IMAGENET_MEAN,
    std: Tuple[float, float, float] = IMAGENET_STD,
) -> Image.Image:
    """
    Inverts ImageNet normalization and converts normalized (3, H, W) tensor back to PIL Image.
    Useful for visual quality verification and preview grid generation.
    """
    t = tensor.detach().cpu().clone()
    for channel, m, s in zip(t, mean, std):
        channel.mul_(s).add_(m)

    t = torch.clamp(t, 0.0, 1.0)
    np_arr = (t.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
    return Image.fromarray(np_arr)

