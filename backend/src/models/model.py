"""
Model architecture: MobileNetV2-based transfer learning for binary classification.
"""
import tensorflow as tf
from tensorflow.keras import layers, models


def build_baseline_cnn(input_shape: tuple = (224, 224, 3)) -> tf.keras.Model:
    """
    Build a binary classifier using MobileNetV2 as a frozen feature extractor.

    Architecture:
        MobileNetV2 (ImageNet weights, frozen)
        -> GlobalAveragePooling2D
        -> Dense(128, relu)
        -> Dropout(0.3)
        -> Dense(1, sigmoid)   [binary: Cat=0, Dog=1]

    Args:
        input_shape: Shape of input images (H, W, C)

    Returns:
        Compiled Keras model
    """
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # Freeze base for transfer learning

    model = models.Sequential(
        [
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(1, activation="sigmoid"),
        ],
        name="cats_vs_dogs_mobilenetv2",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    return model
