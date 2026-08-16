"""
Unit tests for data preprocessing functions (M3 – Automated Testing).
Tests: load_and_resize_image, preprocess_and_split
"""
import io
from pathlib import Path

import pytest
from PIL import Image

from src.data.preprocess import IMG_SIZE, load_and_resize_image, preprocess_and_split


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_image_bytes() -> bytes:
    """Return bytes of a small synthetic RGB image."""
    img = Image.new("RGB", (300, 300), color=(120, 60, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def raw_dataset(tmp_path: Path) -> Path:
    """Create a tiny synthetic raw dataset: 5 cats + 5 dogs."""
    for cls in ["Cat", "Dog"]:
        cls_dir = tmp_path / "raw" / cls
        cls_dir.mkdir(parents=True)
        for i in range(5):
            img = Image.new("RGB", (300, 300), color=(i * 40, i * 20, 100))
            img.save(cls_dir / f"{cls.lower()}_{i}.jpg")
    return tmp_path / "raw"


# ── Tests: load_and_resize_image ──────────────────────────────────────────────
def test_load_and_resize_returns_pil_image(tmp_path):
    """load_and_resize_image should return a PIL Image."""
    img_path = tmp_path / "test.jpg"
    Image.new("RGB", (300, 300)).save(img_path)
    result = load_and_resize_image(img_path)
    assert isinstance(result, Image.Image)


def test_load_and_resize_correct_size(tmp_path):
    """Resized image should be exactly IMG_SIZE."""
    img_path = tmp_path / "test.jpg"
    Image.new("RGB", (400, 600)).save(img_path)
    result = load_and_resize_image(img_path)
    assert result.size == IMG_SIZE


def test_load_and_resize_rgb_mode(tmp_path):
    """Image should be converted to RGB even if source is grayscale."""
    img_path = tmp_path / "gray.jpg"
    Image.new("L", (300, 300)).save(img_path)
    result = load_and_resize_image(img_path)
    assert result.mode == "RGB"


# ── Tests: preprocess_and_split ───────────────────────────────────────────────
def test_preprocess_creates_split_directories(raw_dataset, tmp_path):
    """All train/val/test directories for cats and dogs must be created."""
    processed_dir = tmp_path / "processed"
    preprocess_and_split(str(raw_dataset), str(processed_dir))

    for split in ["train", "val", "test"]:
        for cls in ["cats", "dogs"]:
            assert (processed_dir / split / cls).exists(), \
                f"Missing: {split}/{cls}"


def test_preprocess_images_are_correct_size(raw_dataset, tmp_path):
    """All processed images must be 224x224."""
    processed_dir = tmp_path / "processed"
    preprocess_and_split(str(raw_dataset), str(processed_dir))

    for split in ["train", "val", "test"]:
        for cls in ["cats", "dogs"]:
            imgs = list((processed_dir / split / cls).glob("*.jpg"))
            for img_path in imgs:
                img = Image.open(img_path)
                assert img.size == IMG_SIZE, \
                    f"Wrong size {img.size} for {img_path}"


def test_preprocess_returns_counts(raw_dataset, tmp_path):
    """preprocess_and_split should return a non-empty counts dict."""
    processed_dir = tmp_path / "processed"
    counts = preprocess_and_split(str(raw_dataset), str(processed_dir))
    assert isinstance(counts, dict)
    assert len(counts) == 3  # train, val, test


def test_preprocess_total_images_conserved(raw_dataset, tmp_path):
    """Total processed images per class must equal source image count."""
    processed_dir = tmp_path / "processed"
    counts = preprocess_and_split(str(raw_dataset), str(processed_dir))

    total_cats = sum(counts[s].get("cats", 0) for s in counts)
    total_dogs = sum(counts[s].get("dogs", 0) for s in counts)

    # Each class has 5 source images; all should be processed
    assert total_cats == 5
    assert total_dogs == 5
