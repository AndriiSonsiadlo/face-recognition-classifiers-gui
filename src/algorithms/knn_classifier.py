import math
from pathlib import Path
from typing import Optional

import numpy as np

from algorithms.classifier_base import ClassifierBase
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class KNNClassifier(ClassifierBase):
    """K-Nearest Neighbors classifier for face recognition."""

    def __init__(self, model_path: Path, n_neighbors: Optional[int] = None,
                 weight: str = "distance", verbose: bool = True):
        super().__init__("KNN", model_path, verbose)
        self.n_neighbors = n_neighbors
        self.weight = weight if weight in ("distance", "uniform") else "distance"
        self.knn_algo = "ball_tree"
        self.threshold = 0.6

    def train(self) -> bool:
        """Train KNN classifier."""
        if not self._load_training_data():
            logger.warning("No training data found")
            return False

        if not self.train_data:
            logger.warning("No face encodings found in training data")
            return False

        x_train, y_train = self._prepare_training_data()

        if self.n_neighbors is None or self.n_neighbors < 1:
            self.n_neighbors = int(round(math.sqrt(len(x_train))))
            logger.info(f"Auto-selected n_neighbors: {self.n_neighbors}")

        try:
            from sklearn.neighbors import KNeighborsClassifier
            self.classifier = KNeighborsClassifier(
                n_neighbors=self.n_neighbors,
                algorithm=self.knn_algo,
                weights=self.weight
            )
            self.classifier.fit(x_train, y_train)

            if self.test_data:
                self.evaluate()
            else:
                logger.warning("No test data available")

            return self.save_model()
        except Exception as e:
            logger.error(f"Error training KNN: {e}")
            return False

    def predict(self, encoding: np.ndarray) -> str:
        """Predict label with distance threshold."""
        if self.classifier is None:
            raise ValueError("Classifier not trained")

        try:
            distances, indices = self.classifier.kneighbors([encoding], n_neighbors=1)

            if distances[0][0] <= self.threshold:
                return self.classifier.predict([encoding])[0]
            else:
                return self.UNKNOWN_LABEL

        except Exception as e:
            logger.exception(f"Error predicting with KNN: {e}")
            return self.UNKNOWN_LABEL

    def set_threshold(self, threshold: float) -> None:
        """Set the distance threshold for face matching."""
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold
        logger.info(f"Set KNN threshold to {threshold}")
