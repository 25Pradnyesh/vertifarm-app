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
import json
import os
from pathlib import Path
import time
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dataset_processed"
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


def get_data_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    train_transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    val_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

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
) -> Tuple[float, float, float]:
    model.train()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(labels.cpu().numpy())

    epoch_loss = total_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_targets, all_preds)
    epoch_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return epoch_loss, epoch_acc, epoch_f1


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float, float, np.ndarray, np.ndarray]:
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(labels.cpu().numpy())

    eval_loss = total_loss / len(dataloader.dataset)
    eval_acc = accuracy_score(all_targets, all_preds)
    eval_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return eval_loss, eval_acc, eval_f1, np.array(all_targets), np.array(all_preds)


def train_classifier(
    data_dir: Path = DATA_DIR,
    output_dir: Path = MODELS_DIR,
    epochs: int = 15,
    batch_size: int = 32,
    learning_rate: float = 5e-4,
    weight_decay: float = 1e-2,
    patience: int = 6,
    seed: int = 42,
) -> Dict[str, any]:
    torch.manual_seed(seed)
    np.random.seed(seed)

    print("=" * 60)
    print("VERTIFARM MOBILENETV3-SMALL MODEL TRAINING")
    print(f"Dataset: {data_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Max epochs: {epochs}, Batch size: {batch_size}, LR: {learning_rate}")
    print("=" * 60)

    device = get_device()
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(f"Missing train or val directory in {data_dir}")

    train_transform, val_transform = get_data_transforms()
    train_dataset = ImageFolder(root=str(train_dir), transform=train_transform)
    val_dataset = ImageFolder(root=str(val_dir), transform=val_transform)

    # Verify class ordering matches deterministic order
    print(f"Classes indexed: {train_dataset.class_to_idx}")
    assert list(train_dataset.class_to_idx.keys()) == CLASS_NAMES, (
        f"Unexpected class list: {list(train_dataset.class_to_idx.keys())}"
    )

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
    best_model_path = output_dir / "mobilenet_v3_small_plant_disease.pth"
    history_json_path = output_dir / "training_history.json"
    history_csv_path = output_dir / "training_history.csv"
    metadata_json_path = output_dir / "model_metadata.json"

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

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        curr_lr = optimizer.param_groups[1]["lr"]

        train_loss, train_acc, train_f1 = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc, val_f1, _, _ = evaluate(
            model, val_loader, criterion, device
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
        if val_f1 > best_val_f1:
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
                "class_to_idx": train_dataset.class_to_idx,
                "architecture": "MobileNetV3-Small",
                "imagenet_mean": IMAGENET_MEAN,
                "imagenet_std": IMAGENET_STD,
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
        "class_to_idx": train_dataset.class_to_idx,
        "crop_mapping": CROP_MAPPING,
        "input_dimensions": [3, 224, 224],
        "normalization": {
            "mean": IMAGENET_MEAN,
            "std": IMAGENET_STD,
        },
        "padding_strategy": "ImageNet-mean RGB (124, 116, 104) neutral canvas (maps to 0.0 in tensor space)",
        "training_summary": {
            "best_epoch": best_epoch,
            "best_val_f1": round(best_val_f1, 4),
            "best_val_acc": round(best_val_acc, 4),
            "total_duration_sec": round(total_training_duration, 2),
            "device": str(device),
        },
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
    parser.add_argument("--output", type=Path, default=MODELS_DIR, help="Path to output models directory")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    args = parser.parse_args()

    train_classifier(
        data_dir=args.data,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )
