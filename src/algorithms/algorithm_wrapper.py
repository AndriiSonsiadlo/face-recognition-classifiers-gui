from typing import Tuple

import numpy as np

from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class AlgorithmWrapper:
    def __init__(self, algorithm):
        self.algorithm = algorithm

    def load_model(self) -> bool:
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
        try:
            if hasattr(self.algorithm, 'predict'):
                return self.algorithm.predict(encoding)
            else:
                logger.error("Algorithm does not implement predict()")
                return "Error"
        except Exception as e:
            logger.exception("Error in predict")
            return "Error"

    def set_threshold(self, threshold: float) -> bool:
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

    def is_trained(self) -> bool:
        try:
            return self.algorithm.classifier is not None
        except:
            return False

    def get_accuracy(self) -> float:
        try:
            if hasattr(self.algorithm, 'accuracy'):
                return self.algorithm.accuracy
        except:
            pass
        return 0.0

    def get_model_name(self) -> str:
        try:
            if hasattr(self.algorithm, 'model_name'):
                return self.algorithm.model_name
        except:
            pass
        return "Unknown"

    def __getattr__(self, name: str):
        return getattr(self.algorithm, name)
