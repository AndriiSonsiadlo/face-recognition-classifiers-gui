from typing import List, Optional

from core.enums import Algorithm
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata
from models.model.model_registry import ModelRegistry
from models.model.model_trainer import ModelTrainer

logger = AppLogger().get_logger(__name__)


class ModelService:
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()

    def create_model(
            self, name: str, author: str, algorithm: Algorithm, **params
    ) -> Optional[ModelMetadata]:
        try:
            model = ModelMetadata(
                name=name,
                author=author,
                algorithm=algorithm,
                **params
            )

            if self.registry.add(model):
                logger.info(f"Created model: {name}")
                return model
            else:
                return None

        except Exception as e:
            logger.exception(f"Error creating model {name}: {e}")
            return None

    def train_model(self, model: ModelMetadata):
        trainer = ModelTrainer(model)
        return trainer.train()

    def get_model(self, name: str) -> Optional[ModelMetadata]:
        return self.registry.get(name)

    def get_all_models(self) -> List[ModelMetadata]:
        return self.registry.get_all()

    def search_models(self, query: str) -> List[ModelMetadata]:
        if not query:
            return self.registry.get_all()
        return self.registry.search(query)

    def update_model_threshold(self, name: str, threshold: float) -> Optional[ModelMetadata]:
        try:
            if not 0 <= threshold <= 1:
                logger.error(f"Invalid threshold: {threshold}")
                return None

            model = self.registry.get(name)
            if not model:
                logger.warning(f"Model '{name}' not found")
                return None

            model.threshold = threshold
            if self.registry.save_model(model):
                logger.info(f"Updated threshold for {name} to {threshold}")
                return model
            else:
                return None

        except Exception as e:
            logger.exception(f"Error updating threshold for {name}: {e}")
            return None

    def update_model_comment(self, name: str, comment: str) -> Optional[ModelMetadata]:
        try:
            model = self.registry.get(name)
            if not model:
                logger.warning(f"Model '{name}' not found")
                return None

            model.comment = comment
            if self.registry.save_model(model):
                logger.info(f"Updated comment for {name}")
                return model
            else:
                return None

        except Exception as e:
            logger.exception(f"Error updating comment for {name}: {e}")
            return None

    def delete_model(self, name: str) -> bool:
        try:
            success = self.registry.delete(name)
            if success:
                logger.info(f"Deleted model: {name}")
            return success
        except Exception as e:
            logger.exception(f"Error deleting model {name}: {e}")
            return False

    def update_model_results(
            self,
            name: str,
            learning_time: float,
            accuracy: float,
            train_dataset: List[str],
            test_dataset: List[str],
            count_train: int,
            count_test: int
    ) -> Optional[ModelMetadata]:
        try:
            model = self.registry.get(name)
            if not model:
                logger.warning(f"Model '{name}' not found")
                return None

            model.learning_time = learning_time
            model.accuracy = accuracy
            model.train_dataset_Y = train_dataset
            model.test_dataset_Y = test_dataset
            model.count_train_Y = count_train
            model.count_test_Y = count_test

            if self.registry.save_model(model):
                logger.info(f"Updated results for {name}")
                return model
            else:
                return None

        except Exception as e:
            logger.exception(f"Error updating results for {name}: {e}")
            return None

    def refresh(self) -> None:
        self.registry.refresh()
        logger.info("Refreshed model registry")
