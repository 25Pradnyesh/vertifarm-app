#!/usr/bin/env python3
"""
scripts/train_classifier.py

VertiFarm Plant Disease Classifier Training Script.
Uses transfer learning with MobileNetV3-Small on leak-free preprocessed dataset.

Features:
- Automatic hardware acceleration detection (CUDA, MPS, CPU).
- Pretrained weights initialization (MobileNet_V3_Small_Weights.DEFAULT).
- Deterministic class-index mapping and metadata tracking.
- Moderate, non-destructive data augmentations on training split.
- Cosine annealing learning rate schedule with AdamW optimizer.
- Validation checkpointing tracking Macro F1 score and Accuracy.
- Complete metrics logging to JSON & CSV.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from scripts.augmentations import (
    AugmentationConfig,
    build_eval_transforms,
    build_train_transforms,
    get_augmentation_policy,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dataset_processed"
AUGMENTED_DIR = ROOT / "dataset_augmented"
MODELS_DIR = ROOT / "models"

# Normalized to ImageNet standards
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

CLASS_NAMES = [
    "coriander_bacterial_blight",
    "coriander_healthy",
    "coriander_powdery_mildew",
    "fenugreek_bacterial_blight",
    "fenugreek_cercospora_leaf_spot",
    "fenugreek_healthy",
]

CROP_MAPPING = {
    "coriander_bacterial_blight": {"crop": "Coriander", "disease": "Bacterial Blight", "is_healthy": False},
    "coriander_healthy": {"crop": "Coriander", "disease": "Healthy", "is_healthy": True},
    "coriander_powdery_mildew": {"crop": "Coriander", "disease": "Powdery Mildew", "is_healthy": False},
    "fenugreek_bacterial_blight": {"crop": "Fenugreek", "disease": "Bacterial Blight", "is_healthy": False},
    "fenugreek_cercospora_leaf_spot": {"crop": "Fenugreek", "disease": "Cercospora Leaf Spot", "is_healthy": False},
    "fenugreek_healthy": {"crop": "Fenugreek", "disease": "Healthy", "is_healthy": True},
}


def get_device() -> torch.device:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Hardware detected: CUDA GPU ({torch.cuda.get_device_name(0)})")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Hardware detected: Apple Silicon MPS")
    else:
        device = torch.device("cpu")
        print("Hardware detected: CPU")
    return device


def get_data_transforms(
    config: Optional[AugmentationConfig] = None,
) -> Tuple[transforms.Compose, transforms.Compose]:
    if config is None:
        config = get_augmentation_policy("conservative")
    train_transform = build_train_transforms(config)
    val_transform = build_eval_transforms(config)
    return train_transform, val_transform


def build_model(num_classes: int = 6) -> nn.Module:
    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    max_batches: Optional[int] = None,
) -> Tuple[float, float, float]:
    model.train()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    total_samples = 0

    for b_idx, (images, labels) in enumerate(dataloader):
        if max_batches is not None and b_idx >= max_batches:
            break
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        batch_size = images.size(0)
        total_loss += loss.item() * batch_size
        total_samples += batch_size
        preds = torch.argmax(outputs, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(labels.cpu().numpy())

    epoch_loss = total_loss / max(1, total_samples)
    epoch_acc = accuracy_score(all_targets, all_preds)
    epoch_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return epoch_loss, epoch_acc, epoch_f1


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    max_batches: Optional[int] = None,
) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    total_samples = 0

    with torch.no_grad():
        for b_idx, (images, labels) in enumerate(dataloader):
            if max_batches is not None and b_idx >= max_batches:
                break
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            batch_size = images.size(0)
            total_loss += loss.item() * batch_size
            total_samples += batch_size
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(labels.cpu().numpy())

    eval_loss = total_loss / max(1, total_samples)
    eval_acc = accuracy_score(all_targets, all_preds)
    eval_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return eval_loss, eval_acc, eval_f1, np.array(all_targets), np.array(all_preds)


def compute_file_sha256(filepath: Path) -> str:
    """Calculates SHA-256 hash of a file on disk."""
    if not filepath.exists():
        return "UNKNOWN_FILE_HASH"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def train_classifier(
    data_dir: Path = DATA_DIR,
    augmented_dir: Path = AUGMENTED_DIR,
    output_dir: Path = MODELS_DIR,
    dataset_type: str = "standard",
    epochs: int = 15,
    batch_size: int = 32,
    learning_rate: float = 5e-4,
    weight_decay: float = 1e-2,
    patience: int = 6,
    seed: int = 42,
    policy_name: str = "conservative",
    checkpoint_name: str = "mobilenet_v3_small_conservative_aug.pth",
    rotation_deg: Optional[float] = None,
    flip_v: Optional[float] = None,
    hue_jitter: Optional[float] = None,
    enable_blur: Optional[bool] = None,
    enable_crop: Optional[bool] = None,
    smoke_test: bool = False,
) -> Dict[str, any]:
    torch.manual_seed(seed)
    np.random.seed(seed)

    if smoke_test:
        epochs = 1
        checkpoint_name = "mobilenet_v3_small_smoke_test.pth"
        print("[SMOKE TEST MODE ENABLED] Running fast validation loop on 2 batches.")

    # Initialize augmentation configuration
    aug_config = get_augmentation_policy(policy_name)
    if rotation_deg is not None:
        aug_config.rotation_degrees = rotation_deg
    if flip_v is not None:
        aug_config.vertical_flip_prob = flip_v
    if hue_jitter is not None:
        aug_config.hue_jitter = hue_jitter
    if enable_blur is not None:
        aug_config.enable_blur = enable_blur
    if enable_crop is not None:
        aug_config.enable_random_crop = enable_crop

    device = get_device()
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(f"Missing train or val directory in {data_dir}")

    train_transform, val_transform = get_data_transforms(aug_config)

    # Dataset loading based on dataset_type
    manifest_hash = "UNKNOWN"
    dataset_description = ""

    if dataset_type == "combined":
        if not augmented_dir.exists():
            raise FileNotFoundError(f"Augmented dataset directory not found: {augmented_dir}")
        aug_train_dir = augmented_dir / "train"
        if not aug_train_dir.exists():
            raise FileNotFoundError(f"Missing augmented train directory: {aug_train_dir}")

        orig_dataset = ImageFolder(root=str(train_dir), transform=train_transform)
        aug_dataset = ImageFolder(root=str(aug_train_dir), transform=train_transform)

        assert orig_dataset.class_to_idx == aug_dataset.class_to_idx, (
            f"Class index mismatch: {orig_dataset.class_to_idx} vs {aug_dataset.class_to_idx}"
        )
        assert list(orig_dataset.class_to_idx.keys()) == CLASS_NAMES, (
            f"Unexpected class list: {list(orig_dataset.class_to_idx.keys())}"
        )

        train_dataset = torch.utils.data.ConcatDataset([orig_dataset, aug_dataset])
        class_to_idx = orig_dataset.class_to_idx

        combined_manifest_path = augmented_dir / "combined_train_manifest.csv"
        manifest_hash = compute_file_sha256(combined_manifest_path)
        dataset_description = (
            f"Combined Training Set: {len(orig_dataset)} original source images + "
            f"{len(aug_dataset)} offline augmented derivatives = {len(train_dataset)} total images"
        )

    elif dataset_type == "augmented_only":
        aug_train_dir = augmented_dir / "train"
        train_dataset = ImageFolder(root=str(aug_train_dir), transform=train_transform)
        class_to_idx = train_dataset.class_to_idx
        manifest_path = augmented_dir / "manifest.csv"
        manifest_hash = compute_file_sha256(manifest_path)
        dataset_description = f"Augmented Only: {len(train_dataset)} offline augmented images"

    else:  # standard (original only)
        train_dataset = ImageFolder(root=str(train_dir), transform=train_transform)
        class_to_idx = train_dataset.class_to_idx
        orig_manifest_path = data_dir / "manifest.csv"
        manifest_hash = compute_file_sha256(orig_manifest_path)
        dataset_description = f"Standard Source Dataset: {len(train_dataset)} original images"

    val_dataset = ImageFolder(root=str(val_dir), transform=val_transform)

    print("=" * 65)
    print("VERTIFARM MOBILENETV3-SMALL MODEL TRAINING")
    print(f"Dataset Mode:       {dataset_type} ({dataset_description})")
    print(f"Training Samples:   {len(train_dataset)}")
    print(f"Validation Samples: {len(val_dataset)} (held-out, unaugmented)")
    print(f"Manifest SHA-256:   {manifest_hash}")
    print(f"Target Checkpoint:  {checkpoint_name}")
    print(f"Augmentation:       online_policy='{aug_config.name}' (rot={aug_config.rotation_degrees}°, v_flip={aug_config.vertical_flip_prob}, hue={aug_config.hue_jitter})")
    print(f"Max epochs: {epochs}, Batch size: {batch_size}, LR: {learning_rate}, Seed: {seed}")
    print("=" * 65)

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=False
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=False
    )

    model = build_model(num_classes=len(CLASS_NAMES))
    model.to(device)

    # Optimizer with differential learning rates: backbone 1e-4, head 5e-4
    backbone_params = [p for n, p in model.named_parameters() if "classifier" not in n]
    head_params = [p for n, p in model.named_parameters() if "classifier" in n]

    optimizer = torch.optim.AdamW([
        {"params": backbone_params, "lr": learning_rate * 0.2},
        {"params": head_params, "lr": learning_rate},
    ], weight_decay=weight_decay)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    criterion = nn.CrossEntropyLoss()

    output_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = output_dir / checkpoint_name

    # Preserve baseline artifacts if saving to separate experiment checkpoint
    is_baseline_target = (checkpoint_name == "mobilenet_v3_small_plant_disease.pth")
    file_stem = Path(checkpoint_name).stem if not is_baseline_target else ""
    pfx = f"{file_stem}_" if file_stem else ""

    history_json_path = output_dir / f"{pfx}training_history.json"
    history_csv_path = output_dir / f"{pfx}training_history.csv"
    metadata_json_path = output_dir / f"{pfx}model_metadata.json"

    best_val_f1 = -1.0
    best_val_acc = -1.0
    best_epoch = -1
    epochs_no_improve = 0

    history = {
        "epoch": [],
        "train_loss": [],
        "train_acc": [],
        "train_f1": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
        "lr": [],
        "duration_sec": [],
    }

    start_training_time = time.time()
    batch_limit = 2 if smoke_test else None

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        curr_lr = optimizer.param_groups[1]["lr"]

        train_loss, train_acc, train_f1 = train_one_epoch(
            model, train_loader, criterion, optimizer, device, max_batches=batch_limit
        )
        val_loss, val_acc, val_f1, _, _ = evaluate(
            model, val_loader, criterion, device, max_batches=batch_limit
        )
        scheduler.step()
        duration = time.time() - t0

        history["epoch"].append(epoch)
        history["train_loss"].append(round(train_loss, 4))
        history["train_acc"].append(round(train_acc, 4))
        history["train_f1"].append(round(train_f1, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["val_acc"].append(round(val_acc, 4))
        history["val_f1"].append(round(val_f1, 4))
        history["lr"].append(curr_lr)
        history["duration_sec"].append(round(duration, 2))

        print(
            f"Epoch {epoch:02d}/{epochs:02d} [{duration:.1f}s] - "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.1f}% | Train F1: {train_f1:.4f} || "
            f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.1f}% | Val F1: {val_f1:.4f}"
        )

        # Track best model checkpoint
        if val_f1 > best_val_f1 or smoke_test:
            best_val_f1 = val_f1
            best_val_acc = val_acc
            best_epoch = epoch
            epochs_no_improve = 0

            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_f1": val_f1,
                "val_acc": val_acc,
                "val_loss": val_loss,
                "class_names": CLASS_NAMES,
                "class_to_idx": class_to_idx,
                "architecture": "MobileNetV3-Small",
                "imagenet_mean": IMAGENET_MEAN,
                "imagenet_std": IMAGENET_STD,
                "dataset_type": dataset_type,
                "manifest_sha256": manifest_hash,
            }, best_model_path)
            print(f"  --> [Saved Best Checkpoint] Val F1: {val_f1:.4f} (Acc: {val_acc*100:.1f}%)")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"\nEarly stopping triggered after {epoch} epochs (no improvement for {patience} epochs).")
                break

    total_training_duration = time.time() - start_training_time
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"Total training duration: {total_training_duration:.2f} seconds ({total_training_duration/60:.2f} min)")
    print(f"Best Checkpoint: Epoch {best_epoch} (Val F1: {best_val_f1:.4f}, Val Acc: {best_val_acc*100:.1f}%)")
    print(f"Saved Checkpoint: {best_model_path}")
    print("=" * 60)

    # Save History JSON
    with history_json_path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    # Save History CSV
    with history_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "train_acc", "train_f1", "val_loss", "val_acc", "val_f1", "lr", "duration_sec"])
        for i in range(len(history["epoch"])):
            writer.writerow([
                history["epoch"][i],
                history["train_loss"][i],
                history["train_acc"][i],
                history["train_f1"][i],
                history["val_loss"][i],
                history["val_acc"][i],
                history["val_f1"][i],
                history["lr"][i],
                history["duration_sec"][i],
            ])

    # Save Model Metadata JSON
    metadata = {
        "model_name": "VertiFarm Plant Disease Classifier",
        "architecture": "MobileNetV3-Small",
        "weights_initialization": "MobileNet_V3_Small_Weights.DEFAULT",
        "num_classes": len(CLASS_NAMES),
        "class_names": CLASS_NAMES,
        "class_to_idx": class_to_idx,
        "crop_mapping": CROP_MAPPING,
        "input_dimensions": [3, 224, 224],
        "dataset_configuration": {
            "dataset_type": dataset_type,
            "description": dataset_description,
            "manifest_sha256": manifest_hash,
            "training_samples": len(train_dataset),
            "validation_samples": len(val_dataset),
            "test_samples": 90,
            "classes": CLASS_NAMES,
        },
        "normalization": {
            "mean": list(aug_config.mean),
            "std": list(aug_config.std),
        },
        "padding_strategy": "ImageNet-mean RGB (124, 116, 104) neutral canvas (maps to 0.0 in tensor space)",
        "augmentation": {
            "online_policy_name": aug_config.name,
            "rotation_degrees": aug_config.rotation_degrees,
            "horizontal_flip_prob": aug_config.horizontal_flip_prob,
            "vertical_flip_prob": aug_config.vertical_flip_prob,
            "translate_percent": list(aug_config.translate_percent),
            "scale_range": list(aug_config.scale_range),
            "enable_random_crop": aug_config.enable_random_crop,
            "crop_scale": list(aug_config.crop_scale),
            "brightness_jitter": aug_config.brightness_jitter,
            "contrast_jitter": aug_config.contrast_jitter,
            "saturation_jitter": aug_config.saturation_jitter,
            "hue_jitter": aug_config.hue_jitter,
            "enable_blur": aug_config.enable_blur,
            "blur_prob": aug_config.blur_prob,
            "padding_color": list(aug_config.padding_color),
        },
        "training_summary": {
            "best_epoch": best_epoch,
            "best_val_f1": round(best_val_f1, 4),
            "best_val_acc": round(best_val_acc, 4),
            "total_duration_sec": round(total_training_duration, 2),
            "device": str(device),
            "checkpoint": str(best_model_path.name),
            "seed": seed,
            "smoke_test": smoke_test,
        },
        "scientific_limitation_disclosure": (
            "The 4,200 training files are generated from 420 source images (430 unique leaves overall). "
            "Correlated derivative samples must not be interpreted as independent biological samples. "
            "Generalization evaluation is strictly performed on the 90 unaugmented held-out test set."
        ),
        "uncertainty_threshold": 0.60,
    }

    with metadata_json_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved: {metadata_json_path}")
    print(f"History saved: {history_json_path}")

    return {
        "best_epoch": best_epoch,
        "best_val_f1": best_val_f1,
        "best_val_acc": best_val_acc,
        "total_duration": total_training_duration,
        "checkpoint_path": str(best_model_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MobileNetV3-Small plant disease classifier.")
    parser.add_argument("--data", type=Path, default=DATA_DIR, help="Path to processed dataset")
    parser.add_argument("--augmented-dir", type=Path, default=AUGMENTED_DIR, help="Path to augmented dataset")
    parser.add_argument(
        "--dataset-type",
        type=str,
        default="standard",
        choices=["standard", "combined", "augmented_only"],
        help="Training dataset mode: 'standard' (420 originals), 'combined' (4,200: originals + augmented), or 'augmented_only' (3,780 augmented)",
    )
    parser.add_argument("--output", type=Path, default=MODELS_DIR, help="Path to output models directory")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument(
        "--policy",
        type=str,
        default="conservative",
        help="Online augmentation policy: 'conservative', 'baseline', 'light', 'none'",
    )
    parser.add_argument(
        "--checkpoint-name",
        type=str,
        default="mobilenet_v3_small_conservative_aug.pth",
        help="Checkpoint filename",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--rotation", type=float, default=None, help="Custom rotation degrees")
    parser.add_argument("--flip-v", type=float, default=None, help="Custom vertical flip probability")
    parser.add_argument("--hue-jitter", type=float, default=None, help="Custom hue jitter (max 0.02)")
    parser.add_argument("--smoke-test", action="store_true", help="Run fast 2-batch verification smoke test")
    args = parser.parse_args()

    # If dataset-type is combined and policy was left as default 'conservative',
    # adjust online policy to 'none' unless user explicitly specified otherwise,
    # preventing double-augmenting images as requested in Section 5.
    online_policy = args.policy
    if args.dataset_type == "combined" and args.policy == "conservative":
        online_policy = "none"
        print("[NOTICE] Training on combined offline-augmented dataset. Setting online augmentation policy to 'none' to avoid double augmentation.")

    train_classifier(
        data_dir=args.data,
        augmented_dir=args.augmented_dir,
        output_dir=args.output,
        dataset_type=args.dataset_type,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        policy_name=online_policy,
        checkpoint_name=args.checkpoint_name,
        seed=args.seed,
        rotation_deg=args.rotation,
        flip_v=args.flip_v,
        hue_jitter=args.hue_jitter,
        smoke_test=args.smoke_test,
    )
