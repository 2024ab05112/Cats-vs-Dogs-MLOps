"""
Post-deployment model performance tracking (M5.2).

Sends a small batch of held-out labeled images from the Cats vs Dogs dataset
to the *deployed* /api/predict endpoint and compares predictions against the
true labels, simulating real production traffic with known ground truth.

Usage:
    API_BASE_URL=http://<host>:30800 python -m src.monitoring.post_deploy_eval
"""
import io
import json
import os
import time
from datetime import datetime, timezone

import httpx
import numpy as np
import tensorflow_datasets as tfds
from PIL import Image

CLASS_NAMES = ["Cat", "Dog"]
SAMPLE_SIZE = int(os.environ.get("POST_DEPLOY_SAMPLE_SIZE", "20"))
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
REPORT_PATH = os.environ.get(
    "POST_DEPLOY_REPORT_PATH", "artifacts/post_deploy_performance.json"
)


def load_labeled_sample(n: int):
    """Pull a small held-out slice of the Cats vs Dogs dataset with true labels."""
    ds = tfds.load("cats_vs_dogs", split=f"train[95%:96%]", as_supervised=True)
    samples = []
    for image, label in ds.take(n):
        img = Image.fromarray(image.numpy()).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        samples.append((buf.getvalue(), CLASS_NAMES[int(label.numpy())]))
    return samples


def call_predict(image_bytes: bytes, timeout: float = 15.0) -> str:
    """POST an image to the deployed inference API and return the predicted label."""
    response = httpx.post(
        f"{API_BASE_URL}/api/predict",
        files={"file": ("sample.jpg", image_bytes, "image/jpeg")},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["predicted_label"]


def main():
    print(f"Fetching {SAMPLE_SIZE} labeled samples for post-deploy evaluation...")
    samples = load_labeled_sample(SAMPLE_SIZE)

    results = []
    correct = 0
    latencies = []

    for i, (image_bytes, true_label) in enumerate(samples):
        start = time.time()
        try:
            predicted_label = call_predict(image_bytes)
            error = None
        except Exception as exc:
            predicted_label = None
            error = str(exc)
        latency_ms = round((time.time() - start) * 1000, 2)
        latencies.append(latency_ms)

        is_correct = predicted_label == true_label
        correct += int(is_correct)

        results.append(
            {
                "sample_id": i,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "correct": is_correct,
                "latency_ms": latency_ms,
                "error": error,
            }
        )
        print(
            f"  [{i + 1}/{len(samples)}] true={true_label} "
            f"pred={predicted_label} ({'OK' if is_correct else 'MISS'}) {latency_ms}ms"
        )

    n = len(results)
    accuracy = round(correct / n, 4) if n else 0.0
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_base_url": API_BASE_URL,
        "sample_size": n,
        "accuracy": accuracy,
        "correct": correct,
        "avg_latency_ms": round(float(np.mean(latencies)), 2) if latencies else None,
        "results": results,
    }

    os.makedirs(os.path.dirname(REPORT_PATH) or ".", exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nPost-deploy accuracy: {accuracy:.2%} ({correct}/{n})")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
