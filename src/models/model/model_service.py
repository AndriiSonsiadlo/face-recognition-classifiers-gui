from models.model.model_metadata import ModelMetadata
from models.model.model_trainer import ModelTrainer


class ModelService:
    @staticmethod
    def create_model(name: str, author: str, algorithm: str, **params):
        metadata = ModelMetadata(
            name=name,
            author=author,
            algorithm=algorithm,
            **params
        )
        return metadata

    @staticmethod
    def train_model(metadata: ModelMetadata):
        trainer = ModelTrainer(metadata)
        return trainer.train()
