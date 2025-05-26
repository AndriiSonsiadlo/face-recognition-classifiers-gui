from core.enums import Algorithm
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata

logger = AppLogger().get_logger(__name__)


class AlgorithmFactory:
    @staticmethod
    def create(model: ModelMetadata):
        try:
            from algorithms.algorithm_wrapper import AlgorithmWrapper
            if model.algorithm == Algorithm.KNN:
                from .knn_classifier import KNNClassifier
                return AlgorithmWrapper(
                    KNNClassifier(
                        model_path=model.clf_path,
                        n_neighbors=model.n_neighbors,
                        weight=model.weight
                    )
                )
            elif model.algorithm == Algorithm.SVM:
                from .svm_classifier import SVMClassifier
                return AlgorithmWrapper(
                    SVMClassifier(
                        model_path=model.clf_path,
                        gamma=model.gamma
                    )
                )
            else:
                raise ValueError(f"Unknown algorithm: {model.algorithm}")

        except Exception as e:
            logger.exception(f"Error creating algorithm for {model.name}: {e}")
            raise
