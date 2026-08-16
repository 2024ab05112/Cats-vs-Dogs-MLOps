# Version: 1.0
"""
FastAPI inference service for Cats vs Dogs binary classification.

Endpoints:
  GET  /health          - Liveness / readiness probe
  POST /api/predict     - Upload image, returns label + probabilities
  GET  /api/metrics     - Prometheus metrics (auto-exposed)
  GET  /docs            - Interactive Swagger UI
"""
import io
import logging
import time

from typing import Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from prometheus_fastapi_instrumentator import Instrumentator

# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cats_vs_dogs_api")

# ── App init ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cats vs Dogs Inference API",
    description="Binary image classification service – MLOps Assignment 2",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Model load ─────────────────────────────────────────────────────────────
try:
    import tensorflow as tf

    model = tf.keras.models.load_model("model.h5")
    CLASS_NAMES = ["Cat", "Dog"]
    logger.info("Model loaded successfully.")
except Exception as exc:
    logger.warning(f"Model load failed: {exc}. Running without model.")
    model = None
    CLASS_NAMES = ["Cat", "Dog"]

IMG_SIZE = (224, 224)


# ── Request / Response logging middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    # Exclude sensitive headers; only log method, path, status, latency
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} [{duration}ms]"
    )
    return response


# ── Helpers ────────────────────────────────────────────────────────────────
def preprocess_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decode bytes -> PIL -> resize -> normalize -> batch dimension."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize(IMG_SIZE, Image.LANCZOS)
        arr = np.array(image, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)
    except Exception as exc:
        logger.error(f"Image preprocessing error: {exc}")
        return None


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    """
    Liveness / readiness probe.
    Returns 200 {"status": "healthy"} when the service is ready.
    """
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/api/predict", tags=["Inference"])
async def predict(file: UploadFile = File(...)):
    """
    Accepts a JPEG/PNG image upload and returns binary classification result.

    Returns:
        predicted_label: "Cat" or "Dog"
        confidence:      float [0, 1]
        probabilities:   {"cat": float, "dog": float}
    """
    if model is None:
        return JSONResponse(status_code=503, content={"error": "Model not loaded"})

    content = await file.read()
    logger.info(f"Received file: {file.filename} ({len(content)} bytes)")

    image = preprocess_image(content)
    if image is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image file"})

    prob = float(model.predict(image, verbose=0)[0][0])
    is_dog = prob > 0.5
    label = CLASS_NAMES[int(is_dog)]
    confidence = prob if is_dog else 1.0 - prob

    result = {
        "predicted_label": label,
        "confidence": round(confidence, 4),
        "probabilities": {
            "cat": round(1.0 - prob, 4),
            "dog": round(prob, 4),
        },
    }
    logger.info(f"Prediction: {result}")
    return result


# ── Prometheus instrumentation ─────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/api/metrics")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
