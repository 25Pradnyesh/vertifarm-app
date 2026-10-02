
from pathlib import Path
import random
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset_processed" / "train"
OUTPUT = ROOT / "dataset_processed" / "image_inspection.png"

random.seed(42)
classes = sorted(p for p in DATA.iterdir() if p.is_dir())

fig, axes = plt.subplots(len(classes), 4, figsize=(12, 3 * len(classes)))

for row, class_dir in enumerate(classes):
    images = sorted(class_dir.glob("*.png"))
    chosen = random.sample(images, min(4, len(images)))

    for col, ax in enumerate(axes[row]):
        ax.axis("off")
        if col < len(chosen):
            with Image.open(chosen[col]) as im:
                ax.imshow(im.convert("RGB"))
            ax.set_title(class_dir.name if col == 0 else chosen[col].name[:22],
                         fontsize=8)

plt.tight_layout()
fig.savefig(OUTPUT, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Inspection sheet saved to: {OUTPUT}")