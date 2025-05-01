from pathlib import Path

import numpy as np

from algorithms.classifier_base import ClassifierBase
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class SVMClassifier(ClassifierBase):
    """Support Vector Machine classifier for face recognition."""

    def __init__(self, model_path: Path, gamma: str = "scale", verbose: bool = True):
        super().__init__("SVM", model_path, verbose)
        self.gamma = gamma if gamma in ("auto", "scale") else "scale"

    def train(self) -> bool:
        """Train SVM classifier."""
        if not self._load_training_data():
            logger.warning("No training data found")
            return False

        if not self.train_data:
            logger.warning("No face encodings found in training data")
            return False

        x_train, y_train = self._prepare_training_data()

        try:
            from sklearn.svm import SVC
            self.classifier = SVC(kernel='linear', gamma=self.gamma)
            self.classifier.fit(x_train, y_train)

            if self.test_data:
                self.evaluate()
            else:
                logger.warning("No test data available")

            return self.save_model()
        except Exception as e:
            logger.error(f"Error training SVM: {e}")
            return False

    def predict(self, encoding: np.ndarray) -> str:
        """Predict label for a single face encoding."""
        if self.classifier is None:
            raise ValueError("Classifier not trained")

        try:
            prediction = self.classifier.predict([encoding])[0]
            return prediction
        except Exception as e:
            logger.exception(f"Error predicting with SVM: {e}")
            return self.UNKNOWN_LABEL
