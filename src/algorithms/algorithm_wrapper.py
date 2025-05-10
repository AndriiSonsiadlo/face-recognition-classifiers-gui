from typing import Tuple

import numpy as np

from core import config
from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class AlgorithmWrapper:
    """Wrapper that delegates to specific algorithm implementations.

    Provides a unified interface regardless of underlying algorithm (KNN, SVM, etc.)
    """

    def __init__(self, algorithm):
        """Initialize wrapper.

        Args:
            algorithm: Concrete classifier instance (KNNClassifier, SVMClassifier, etc.)
        """
        self.algorithm = algorithm

    # ============================================================
    # Core Operations
    # ============================================================

    def load_model(self) -> bool:
        """Load model from disk.

        Returns:
            True if successful
        """
        try:
            if hasattr(self.algorithm, 'load_model'):
                return self.algorithm.load_model()
            else:
                logger.error("Algorithm does not implement load_model()")
                return False
        except Exception as e:
            logger.exception("Error loading model")
            return False

    def predict_webcam(self, frame: np.ndarray) -> Tuple[np.ndarray, int, str]:
        """Predict from webcam frame.

        Args:
            frame: Input frame from camera

        Returns:
            Tuple of (annotated_frame, counter, name)
        """
        try:
            if hasattr(self.algorithm, 'predict_webcam'):
                return self.algorithm.predict_webcam(frame)
            else:
                logger.error("Algorithm does not implement predict_webcam()")
                return frame, 0, "Error"
        except Exception as e:
            logger.exception("Error in predict_webcam")
            return frame, 0, "Error"

    def predict_from_image(self, image_path: str) -> Tuple[np.ndarray, str]:
        """Predict from image file.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (annotated_frame, name)
        """
        try:
            if hasattr(self.algorithm, 'predict_from_image'):
                return self.algorithm.predict_from_image(image_path)
            else:
                logger.error("Algorithm does not implement predict_from_image()")
                return np.array([]), "Error"
        except Exception as e:
            logger.exception("Error in predict_from_image")
            return np.array([]), "Error"

    def predict(self, encoding: np.ndarray) -> str:
        """Predict single encoding (low-level).

        Args:
            encoding: Face encoding from face_recognition library

        Returns:
            Predicted person name
        """
        try:
            if hasattr(self.algorithm, 'predict'):
                return self.algorithm.predict(encoding)
            else:
                logger.error("Algorithm does not implement predict()")
                return "Error"
        except Exception as e:
            logger.exception("Error in predict")
            return "Error"

    # ============================================================
    # Configuration
    # ============================================================

    def set_threshold(self, threshold: float) -> bool:
        """Set confidence threshold (if supported).

        Args:
            threshold: Threshold value (0.0 - 1.0)

        Returns:
            True if supported
        """
        try:
            if hasattr(self.algorithm, 'set_threshold'):
                self.algorithm.set_threshold(threshold)
                return True
            else:
                logger.debug("Algorithm does not support set_threshold()")
                return False
        except Exception as e:
            logger.exception("Error setting threshold")
            return False

    # ============================================================
    # State Queries
    # ============================================================

    def is_trained(self) -> bool:
        """Check if model is trained/loaded."""
        try:
            return self.algorithm.classifier is not None
        except:
            return False

    def get_accuracy(self) -> float:
        """Get model accuracy if available."""
        try:
            if hasattr(self.algorithm, 'accuracy'):
                return self.algorithm.accuracy
        except:
            pass
        return 0.0

    def get_model_name(self) -> str:
        """Get model/algorithm name."""
        try:
            if hasattr(self.algorithm, 'model_name'):
                return self.algorithm.model_name
        except:
            pass
        return "Unknown"

    # ============================================================
    # Delegate Methods (for flexibility)
    # ============================================================

    def __getattr__(self, name: str):
        """Delegate unknown attributes to wrapped algorithm."""
        return getattr(self.algorithm, name)
