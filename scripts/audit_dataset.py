
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import json

ROOT = Path(__file__).resolve().parent.parent / "dataset"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

if not ROOT.exists():
    raise SystemExit(f"Dataset folder not found: {ROOT}")

sizes = Counter()
formats = Counter()
class_counts = Counter()
class_sizes = defaultdict(Counter)
aspect_ratios = Counter()
bad_files = []
total_pixels = 0
total_bytes = 0
valid_images = 0

for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in VALID_EXTENSIONS:
        continue

    # Expect: dataset / crop / class / image
    relative = path.relative_to(ROOT)
    parts = relative.parts
    label = " / ".join(parts[:2]) if len(parts) >= 3 else "UNEXPECTED_FOLDER_DEPTH"

    try:
        with Image.open(path) as img:
            img.verify()

        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format or path.suffix.lower().lstrip(".")

        if width < 1 or height < 1:
            raise ValueError("Invalid image dimensions")

        size = f"{width}x{height}"
        sizes[size] += 1
        formats[fmt.upper()] += 1
        class_counts[label] += 1
        class_sizes[label][size] += 1
        aspect_ratios[round(width / height, 2)] += 1
        total_pixels += width * height
        total_bytes += path.stat().st_size
        valid_images += 1

    except (OSError, ValueError, UnidentifiedImageError) as exc:
        bad_files.append({"file": str(relative), "error": str(exc)})

print("\n========== DATASET AUDIT ==========")
print(f"Dataset: {ROOT}")
print(f"Valid images: {valid_images}")
print(f"Unreadable/corrupt images: {len(bad_files)}")
print(f"Total image storage: {total_bytes / (1024**2):.2f} MiB")

print("\n--- Images per class ---")
for label, count in sorted(class_counts.items()):
    print(f"{label}: {count}")

print("\n--- Most common exact dimensions ---")
for dimensions, count in sizes.most_common(20):
    percentage = count / valid_images * 100 if valid_images else 0
    print(f"{dimensions}: {count} images ({percentage:.1f}%)")

print("\n--- Dimensions within each class ---")
for label, counts in sorted(class_sizes.items()):
    print(f"\n{label}")
    for dimensions, count in counts.most_common(5):
        print(f"  {dimensions}: {count}")

print("\n--- File formats ---")
for fmt, count in formats.most_common():
    print(f"{fmt}: {count}")

print("\n--- Common aspect ratios (width / height) ---")
for ratio, count in aspect_ratios.most_common(10):
    print(f"{ratio}: {count}")

if bad_files:
    print("\n--- Unreadable files ---")
    for item in bad_files:
        print(f"{item['file']}: {item['error']}")

report_path = ROOT.parent / "dataset_audit.json"
report_path.write_text(
    json.dumps({
        "dataset_root": str(ROOT),
        "valid_images": valid_images,
        "bad_images": bad_files,
        "dimensions": sizes,
        "formats": formats,
        "class_counts": class_counts,
        "class_dimensions": {
            label: dict(counts)
            for label, counts in class_sizes.items()
        },
        "aspect_ratios": aspect_ratios,
        "total_bytes": total_bytes,
    }, indent=2, default=dict),
    encoding="utf-8",
)

print(f"\nFull audit report saved to: {report_path}")