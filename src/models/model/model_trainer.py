import time

from algorithms.knn_classifier import KNNClassifier
from algorithms.svm_classifier import SVMClassifier
from core import Algorithm
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata

logger = AppLogger().get_logger(__name__)


class ModelTrainer:
    """
    Receives a ModelMetadata object and modifies it.
    """

    def __init__(self, metadata: ModelMetadata):
        self.meta = metadata

    def train(self) -> bool:
        start_time = time.time()
        algo = self.meta.algorithm

        if algo == Algorithm.KNN:
            clf = KNNClassifier(
                model_path=self.meta.clf_path,
                n_neighbors=self.meta.n_neighbors,
                weight=self.meta.weight,
            )
        elif algo == Algorithm.SVM:
            clf = SVMClassifier(
                model_path=self.meta.clf_path,
                gamma=self.meta.gamma,
            )
        else:
            logger.error(f"Chosen invalid algorithm: {algo}")
            return False

        try:
            ok = clf.train()
        except Exception as e:
            logger.error(f"Training failed due to internal error: {e}")
            return False

        if ok:
            self.meta.learning_time = round(time.time() - start_time, 2)
            self.meta.train_dataset_Y = clf.train_persons
            self.meta.test_dataset_Y = clf.test_persons
            self.meta.accuracy = clf.accuracy

            self.meta.save()

        return ok
