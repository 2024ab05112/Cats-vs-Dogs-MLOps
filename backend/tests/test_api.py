"""
Unit tests for FastAPI inference endpoints (M3 – Automated Testing).
Tests: /health, /api/predict
Uses mocking to avoid loading a real model.
"""
import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image


# ── Mock model BEFORE importing main ─────────────────────────────────────────
with patch("tensorflow.keras.models.load_model") as mock_load:
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.85]])  # Dog (>0.5)
    mock_load.return_value = mock_model
    from main import app  # noqa: E402

client = TestClient(app)


def _make_image_bytes(width: int = 224, height: int = 224) -> bytes:
    """Create a synthetic JPEG image in memory."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


# ── Health endpoint ───────────────────────────────────────────────────────────
def test_health_returns_200():
    """GET /health should return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_healthy_status():
    """GET /health body must contain status=healthy."""
    response = client.get("/health")
    assert response.json()["status"] == "healthy"


def test_health_reports_model_loaded():
    """GET /health body must contain model_loaded field."""
    response = client.get("/health")
    assert "model_loaded" in response.json()


# ── Predict endpoint ──────────────────────────────────────────────────────────
def test_predict_returns_200():
    """POST /api/predict with valid image should return HTTP 200."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200


def test_predict_returns_label():
    """Response must contain predicted_label ('Cat' or 'Dog')."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    body = response.json()
    assert "predicted_label" in body
    assert body["predicted_label"] in ("Cat", "Dog")


def test_predict_returns_confidence():
    """Response confidence must be a float between 0 and 1."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    body = response.json()
    assert "confidence" in body
    assert 0.0 <= body["confidence"] <= 1.0


def test_predict_returns_probabilities():
    """Response must contain cat and dog probabilities."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    body = response.json()
    assert "probabilities" in body
    assert "cat" in body["probabilities"]
    assert "dog" in body["probabilities"]


def test_predict_probabilities_sum_to_one():
    """Cat + Dog probabilities must sum to ~1.0."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    probs = response.json()["probabilities"]
    assert abs(probs["cat"] + probs["dog"] - 1.0) < 0.01


def test_predict_dog_label_for_high_prob():
    """With mock probability 0.85, label should be Dog."""
    img_bytes = _make_image_bytes()
    response = client.post(
        "/api/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.json()["predicted_label"] == "Dog"
