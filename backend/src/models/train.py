"""
Training pipeline with MLflow experiment tracking.
Reads hyperparameters from params.yaml and logs all artifacts.
"""
import os

import mlflow
import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
import yaml

from src.models.model import build_baseline_cnn
from src.utils.metrics import plot_confusion_matrix, plot_loss_curves

# ── Load hyperparams from params.yaml ───────────────────────────────────────
with open("params.yaml", "r") as f:
    PARAMS = yaml.safe_load(f)

EPOCHS = PARAMS["epochs"]
BATCH_SIZE = PARAMS["batch_size"]
IMG_SIZE = (PARAMS["image_size"], PARAMS["image_size"])
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

# ── MLflow setup ─────────────────────────────────────────────────────────────
try:
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("cats_vs_dogs_classification")
    MLFLOW_AVAILABLE = True
except Exception as exc:
    print(f"WARNING: MLflow setup failed: {exc}. Training locally without tracking.")
    MLFLOW_AVAILABLE = False


def preprocess(image, label):
    """Resize + normalize a single image tensor."""
    image = tf.image.resize(image, IMG_SIZE)
    image = tf.cast(image, tf.float32) / 255.0
    return image, label


def augment(image, label):
    """Apply random augmentation to training images."""
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.1)
    image = tf.image.random_contrast(image, lower=0.9, upper=1.1)
    return image, label


def build_datasets():
    """Download Cats vs Dogs via TFDS and build train/val/test tf.data pipelines."""
    print("Loading Cats vs Dogs dataset via TensorFlow Datasets...")

    # Use 80% for train, 10% for val, 10% for test
    train_ds_raw, _ = tfds.load(
        "cats_vs_dogs",
        split="train[:80%]",
        as_supervised=True,
        with_info=True,
    )
    val_ds_raw = tfds.load("cats_vs_dogs", split="train[80%:90%]", as_supervised=True)
    test_ds_raw = tfds.load("cats_vs_dogs", split="train[90%:]", as_supervised=True)

    # Preprocess + augment
    train_ds = (
        train_ds_raw
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .map(augment, num_parallel_calls=tf.data.AUTOTUNE)
        .shuffle(2000, seed=42)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )
    val_ds = (
        val_ds_raw
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )
    test_ds = (
        test_ds_raw
        .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )

    return train_ds, val_ds, test_ds


def main():
    train_ds, val_ds, test_ds = build_datasets()
    model = build_baseline_cnn()

    # ── Train ────────────────────────────────────────────────────────────
    history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)

    # ── Evaluate on test set ─────────────────────────────────────────────
    test_loss, test_acc = model.evaluate(test_ds)
    print(f"\nTest Accuracy: {test_acc:.4f}  |  Test Loss: {test_loss:.4f}")

    # ── Confusion matrix ─────────────────────────────────────────────────
    y_true, y_pred = [], []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend((preds > 0.5).astype(int).flatten())

    os.makedirs("artifacts", exist_ok=True)
    cm_path = "artifacts/confusion_matrix.png"
    plot_confusion_matrix(
        y_true=np.array(y_true),
        y_pred=np.array(y_pred),
        class_names=["Cat", "Dog"],
        save_path=cm_path,
    )

    # ── Loss / accuracy curves ───────────────────────────────────────────
    curves_path = "artifacts/training_curves.png"
    plot_loss_curves(history, save_path=curves_path)

    # ── Save model ───────────────────────────────────────────────────────
    model.save("model.h5")
    print("Model saved locally as model.h5")

    # ── Log to MLflow if available ───────────────────────────────────────
    try:
        if MLFLOW_AVAILABLE:
            with mlflow.start_run():
                mlflow.log_params(
                    {
                        "epochs": EPOCHS,
                        "batch_size": BATCH_SIZE,
                        "image_size": IMG_SIZE[0],
                        "optimizer": PARAMS.get("optimizer", "adam"),
                        "base_model": "MobileNetV2",
                        "learning_rate": 0.0001,
                        "dropout": 0.3,
                    }
                )
                for epoch in range(EPOCHS):
                    mlflow.log_metrics(
                        {
                            "train_accuracy": history.history["accuracy"][epoch],
                            "val_accuracy": history.history["val_accuracy"][epoch],
                            "train_loss": history.history["loss"][epoch],
                            "val_loss": history.history["val_loss"][epoch],
                        },
                        step=epoch,
                    )
                mlflow.log_metrics({"test_accuracy": test_acc, "test_loss": test_loss})
                mlflow.log_artifact(cm_path)
                mlflow.log_artifact(curves_path)
                mlflow.log_artifact("model.h5")
                print("Logged run to MLflow.")
    except Exception as exc:
        print(f"Skipping MLflow logging: {exc}")


if __name__ == "__main__":
    main()
