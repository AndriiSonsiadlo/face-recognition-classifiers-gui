import time

from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from core.config import config
from models.model.model_metadata import ModelMetadata
from utils.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class ModelTrainer:
    """
    Pure ML logic.
    Receives a ModelMetadata object and modifies it.
    """

    def __init__(self, metadata: ModelMetadata):
        self.meta = metadata

    def train(self) -> bool:
        start_time = time.time()
        algo = self.meta.algorithm

        # Select classifier
        model_path = config.paths.get_file_model(self.meta)
        if algo == config.model.ALGORITHM_KNN:
            clf = KNNClassifier(
                model_path=model_path,
                n_neighbors=self.meta.n_neighbors,
                weight=self.meta.weight,
            )
        else:
            clf = SVMClassifier(
                model_path=model_path,
                gamma=self.meta.gamma,
            )

        # Execute training
        try:
            ok = clf.train()
        except Exception as e:
            logger.error(f"Training failed due to internal error: {e}")
            return False

        # If successful → fill metadata fields (PURE TRANSFER of results)
        if ok:
            self.meta.learning_time = round(time.time() - start_time, 2)
            self.meta.train_dataset_Y = clf.train_persons
            self.meta.test_dataset_Y = clf.test_persons
            self.meta.count_train_Y = clf.count_train_persons
            self.meta.count_test_Y = clf.count_test_persons
            self.meta.accuracy = clf.accuracy

            # Save metadata only (no model saving here)
            self.meta.save_json()

        return ok
