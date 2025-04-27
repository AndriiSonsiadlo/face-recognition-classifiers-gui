from core import config
from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from utils.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class AlgorithmWrapper:
    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config
        self.algorithm = None

    def load(self) -> bool:
        """Instantiate and load selected algorithm. Returns True on success."""
        alg = self.model_config.algorithm
        if alg == config.model.ALGORITHM_KNN:
            self.algorithm = KNNClassifier(self.model_config, self.model_config.path_file_model)
        elif alg == config.model.ALGORITHM_SVM:
            self.algorithm = SVMClassifier(self.model_config, self.model_config.path_file_model)
        else:
            logger.error("Unknown algorithm type: %s", alg)
            return False

        try:
            return self.algorithm.load_model()
        except Exception:
            logger.exception("Failed to load model")
            return False

    def predict_webcam(self, frame):
        if not self.algorithm:
            raise RuntimeError("Algorithm not loaded")
        return self.algorithm.predict_webcam(frame)
