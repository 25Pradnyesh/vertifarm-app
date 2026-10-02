
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import csv
import math

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dataset"
OUTPUT = ROOT / "dataset_review"
SHEET_DIR = OUTPUT / "contact_sheets"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# Layout: 10 columns x 10 rows for 100 images per class.
COLUMNS = 10
THUMB_W = 140
THUMB_H = 115
LABEL_H = 34
CELL_W = THUMB_W
CELL_H = THUMB_H + LABEL_H
HEADER_H = 65

CLASS_MAP = {
    ("Coriander", "Bacterial Blight"): "coriander_bacterial_blight",
    ("Coriander", "Coriander Healthy"): "coriander_healthy",
    ("Coriander", "Powdery Mildew"): "coriander_powdery_mildew",
    ("Fenugreek", "Bacterial blight"): "fenugreek_bacterial_blight",
    ("Fenugreek", "Cercospora leaf spot"): "fenugreek_cercospora_leaf_spot",
    ("Fenugreek", "Fenugreek Healthy"): "fenugreek_healthy",
}

if not SOURCE.exists():
    raise SystemExit(f"Dataset not found: {SOURCE}")

SHEET_DIR.mkdir(parents=True, exist_ok=True)
review_rows = []

for (crop, original_class), label in CLASS_MAP.items():
    folder = SOURCE / crop / original_class

    if not folder.is_dir():
        raise SystemExit(f"Expected folder not found: {folder}")

    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    )

    rows = math.ceil(len(files) / COLUMNS)
    sheet = Image.new(
        "RGB",
        (COLUMNS * CELL_W, HEADER_H + rows * CELL_H),
        "white",
    )
    draw = ImageDraw.Draw(sheet)

    draw.text((12, 10), label, fill="black")
    draw.text(
        (12, 32),
        f"Images: {len(files)} | Original class: {crop} / {original_class}",
        fill="black",
    )

    for index, path in enumerate(files):
        x = (index % COLUMNS) * CELL_W
        y = HEADER_H + (index // COLUMNS) * CELL_H

        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                original_size = f"{im.width}x{im.height}"
                im.thumbnail(
                    (THUMB_W - 8, THUMB_H - 8),
                    Image.Resampling.LANCZOS,
                )

                # White background; no cropping or distortion.
                preview = Image.new("RGB", (THUMB_W, THUMB_H), "white")
                px = (THUMB_W - im.width) // 2
                py = (THUMB_H - im.height) // 2
                preview.paste(im, (px, py))
                sheet.paste(preview, (x, y))

        except Exception as exc:
            original_size = "UNREADABLE"
            draw.text((x + 5, y + 10), "IMAGE ERROR", fill="red")
            print(f"Could not preview {path}: {exc}")

        # Index makes images easy to identify in the CSV.
        draw.text(
            (x + 4, y + THUMB_H + 2),
            f"#{index + 1:03d} {path.name[:17]}",
            fill="black",
        )
        draw.text(
            (x + 4, y + THUMB_H + 17),
            original_size,
            fill="gray",
        )

        review_rows.append({
            "image_id": f"{label}_{index + 1:03d}",
            "crop": crop,
            "current_label": label,
            "original_class_folder": original_class,
            "filename": path.name,
            "source_path": str(path.relative_to(ROOT)),
            "original_dimensions": original_size,
            "decision": "unreviewed",
            "correct_label_if_wrong": "",
            "notes": "",
        })

    sheet_path = SHEET_DIR / f"{label}.jpg"
    sheet.save(sheet_path, quality=92)
    print(f"Created: {sheet_path}")

csv_path = OUTPUT / "image_review.csv"

with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=review_rows[0].keys())
    writer.writeheader()
    writer.writerows(review_rows)

print("\n========== REVIEW FILES CREATED ==========")
print(f"Images indexed: {len(review_rows)}")
print(f"Contact sheets: {SHEET_DIR}")
print(f"Review CSV: {csv_path}")
print("\nCSV decision values:")
print("  unreviewed = not checked yet")
print("  keep       = image and label appear appropriate")
print("  review     = uncertain; needs closer inspection")
print("  exclude    = unsuitable image or confirmed bad label")
print("\nNo source images were modified or deleted.")