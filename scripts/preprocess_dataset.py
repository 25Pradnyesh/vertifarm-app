
from collections import Counter
from pathlib import Path
import csv
import json
import random

from PIL import Image, ImageOps, UnidentifiedImageError
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dataset"
OUTPUT = ROOT / "dataset_processed"
IMAGE_SIZE = 224
SEED = 42

# Explicit mapping prevents the crop folders from being
# incorrectly treated as the only two classes.
CLASS_MAP = {
    ("Coriander", "Bacterial Blight"): "coriander_bacterial_blight",
    ("Coriander", "Coriander Healthy"): "coriander_healthy",
    ("Coriander", "Powdery Mildew"): "coriander_powdery_mildew",
    ("Fenugreek", "Bacterial blight"): "fenugreek_bacterial_blight",
    ("Fenugreek", "Cercospora leaf spot"): "fenugreek_cercospora_leaf_spot",
    ("Fenugreek", "Fenugreek Healthy"): "fenugreek_healthy",
}

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

if not SOURCE.exists():
    raise SystemExit(f"Source dataset not found: {SOURCE}")

# Refuse to overwrite an existing output dataset.
if OUTPUT.exists() and any(OUTPUT.iterdir()):
    raise SystemExit(
        f"Output already contains files: {OUTPUT}\n"
        "Rename or remove that output directory before rerunning."
    )

OUTPUT.mkdir(parents=True, exist_ok=True)

records = []
bad_images = []

for (crop, original_class), label in CLASS_MAP.items():
    folder = SOURCE / crop / original_class

    if not folder.is_dir():
        raise SystemExit(f"Expected class folder not found: {folder}")

    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    )

    if not files:
        raise SystemExit(f"No images found in {folder}")

    for path in files:
        try:
            with Image.open(path) as im:
                im.verify()

            with Image.open(path) as im:
                width, height = im.size

            records.append({
                "source": path,
                "crop": crop.lower(),
                "label": label,
                "original_width": width,
                "original_height": height,
            })

        except (OSError, ValueError, UnidentifiedImageError) as exc:
            bad_images.append({
                "source": str(path.relative_to(ROOT)),
                "error": str(exc),
            })

# Split separately within each class for balanced representation.
train_records, val_records, test_records = [], [], []

for label in sorted(CLASS_MAP.values()):
    group = [r for r in records if r["label"] == label]

    if len(group) < 3:
        raise SystemExit(f"Too few readable images for class {label}")

    train, temporary = train_test_split(
        group,
        test_size=0.30,
        random_state=SEED,
        shuffle=True,
    )

    val, test = train_test_split(
        temporary,
        test_size=0.50,
        random_state=SEED,
        shuffle=True,
    )

    train_records.extend(train)
    val_records.extend(val)
    test_records.extend(test)

random.Random(SEED).shuffle(train_records)
random.Random(SEED).shuffle(val_records)
random.Random(SEED).shuffle(test_records)

splits = {
    "train": train_records,
    "val": val_records,
    "test": test_records,
}

manifest = []
processed_failures = []

for split, items in splits.items():
    for record in items:
        source = record["source"]
        label = record["label"]

        # Unique filename avoids collisions between source folders.
        filename = f"{source.stem}_{source.parent.name}{source.suffix}.png"
        destination = OUTPUT / split / label / filename
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(source) as im:
                # Respect EXIF rotation before measuring/resizing.
                im = ImageOps.exif_transpose(im).convert("RGB")

                # Scale to fit within 224x224, preserving aspect ratio.
                im.thumbnail(
                    (IMAGE_SIZE, IMAGE_SIZE),
                    Image.Resampling.LANCZOS,
                )

                # Neutral padding; no stretching or cropping.
                canvas = Image.new(
                    "RGB",
                    (IMAGE_SIZE, IMAGE_SIZE),
                    (0, 0, 0),
                )
                x = (IMAGE_SIZE - im.width) // 2
                y = (IMAGE_SIZE - im.height) // 2
                canvas.paste(im, (x, y))
                canvas.save(destination, format="PNG", optimize=True)

            manifest.append({
                "split": split,
                "crop": record["crop"],
                "label": label,
                "source": str(source.relative_to(ROOT)),
                "output": str(destination.relative_to(ROOT)),
                "original_width": record["original_width"],
                "original_height": record["original_height"],
                "processed_width": IMAGE_SIZE,
                "processed_height": IMAGE_SIZE,
            })

        except (OSError, ValueError, UnidentifiedImageError) as exc:
            processed_failures.append({
                "source": str(source.relative_to(ROOT)),
                "error": str(exc),
            })

# Save provenance and split information.
manifest_path = OUTPUT / "manifest.csv"
if manifest:
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
        writer.writeheader()
        writer.writerows(manifest)

report = {
    "source_images_readable": len(records),
    "source_images_unreadable": bad_images,
    "preprocessing_failures": processed_failures,
    "image_size": [IMAGE_SIZE, IMAGE_SIZE],
    "format": "PNG",
    "color_mode": "RGB",
    "resize": "Aspect-ratio-preserving fit with black padding",
    "seed": SEED,
    "split_counts": {
        split: len(items) for split, items in splits.items()
    },
    "class_counts": {
        split: dict(Counter(r["label"] for r in items))
        for split, items in splits.items()
    },
    "manifest": str(manifest_path),
}

(OUTPUT / "preprocessing_report.json").write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print("\n========== PREPROCESSING SUMMARY ==========")
print(f"Source images readable: {len(records)}")
print(f"Source images unreadable: {len(bad_images)}")
print(f"Processed successfully: {len(manifest)}")
print(f"Preprocessing failures: {len(processed_failures)}")
print(f"Image dimensions: {IMAGE_SIZE}x{IMAGE_SIZE}")
print(f"Output: {OUTPUT}")

for split in splits:
    print(f"\n{split.upper()}: {len(splits[split])} assigned")
    print("Successfully written by class:")
    counts = Counter(
        row["label"] for row in manifest if row["split"] == split
    )
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")

if bad_images:
    print("\nWARNING: Some source images could not be read.")
    for item in bad_images:
        print(item)

if processed_failures:
    print("\nWARNING: Some images failed during preprocessing.")
    for item in processed_failures:
        print(item)

if len(manifest) != len(records) or bad_images or processed_failures:
    print("\nReview the report before training.")
else:
    print("\nPreprocessing completed without image-processing failures.")