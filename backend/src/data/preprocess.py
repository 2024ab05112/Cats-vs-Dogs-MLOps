    """
Data preprocessing module for Cats vs Dogs dataset.
Resizes images to 224x224, converts to RGB, and splits into train/val/test.
"""
import os
import random
from pathlib import Path

from PIL import Image
from tqdm import tqdm

IMG_SIZE = (224, 224)
SPLITS = {"train": 0.8, "val": 0.1, "test": 0.1}

RAW_CLASS_MAP = {
    "Cat": "cats",
    "Dog": "dogs",
}


def load_and_resize_image(img_path: Path, size: tuple = IMG_SIZE) -> Image.Image:
    """Load an image from disk, convert to RGB, and resize to `size`."""
    img = Image.open(img_path).convert("RGB")
    img = img.resize(size, Image.LANCZOS)
    return img


def preprocess_and_split(raw_dir: str, processed_dir: str, seed: int = 42) -> dict:
    """
    Preprocess raw images and split into train/val/test sets.

    Args:
        raw_dir:       Root directory containing class sub-dirs (Cat/, Dog/)
        processed_dir: Output directory for split/processed images
        seed:          Random seed for reproducible splits

    Returns:
        counts dict: {split: {class: count}}
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    random.seed(seed)

    counts: dict = {split: {} for split in SPLITS}

    for raw_cls, out_cls in RAW_CLASS_MAP.items():
        # Create output directories
        for split in SPLITS:
            (processed_dir / split / out_cls).mkdir(parents=True, exist_ok=True)

        images = list((raw_dir / raw_cls).glob("*.jpg"))
        if not images:
            print(f"WARNING: No .jpg images found in {raw_dir / raw_cls}")
            continue

        random.shuffle(images)
        n_total = len(images)
        n_train = int(n_total * SPLITS["train"])
        n_val = int(n_total * SPLITS["val"])

        split_map = {
            "train": images[:n_train],
            "val": images[n_train : n_train + n_val],
            "test": images[n_train + n_val :],
        }

        for split, split_imgs in split_map.items():
            saved = 0
            for img_path in tqdm(split_imgs, desc=f"{raw_cls} -> {split}"):
                try:
                    img = load_and_resize_image(img_path)
                    out_path = processed_dir / split / out_cls / img_path.name
                    img.save(out_path)
                    saved += 1
                except Exception as exc:
                    print(f"Error processing {img_path}: {exc}")
            counts[split][out_cls] = saved

    print("\n=== Preprocessing Summary ===")
    for split, cls_counts in counts.items():
        print(f"  {split}: {cls_counts}")

    return counts


if __name__ == "__main__":
    preprocess_and_split(
        raw_dir="data/raw",
        processed_dir="data/processed",
    )
