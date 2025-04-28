from datetime import datetime
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, NonNegativeInt, NonNegativeFloat, Field

from core import Algorithm, config, AppLogger

logger = AppLogger().get_logger(__name__)


class ModelMetadata(BaseModel):
    name: str
    author: str = "Unknown"
    comment: str = ""
    created_at: datetime = datetime.now()
    learning_time: NonNegativeInt

    algorithm: Algorithm
    accuracy: NonNegativeFloat
    threshold: NonNegativeFloat

    n_neighbors: Optional[NonNegativeInt] = None
    weight: Optional[str] = None
    gamma: Optional[str] = None

    train_dataset_Y: List = Field(default_factory=list)
    test_dataset_Y: List = Field(default_factory=list)

    @property
    def created_format(self) -> str:
        return self.created_at.strftime("%d %b %Y at %H:%M")

    @property
    def dir_path(self) -> Path:
        return config.paths.MODEL_DATA_DIR / self.name

    @property
    def clf_path(self) -> Path:
        return self.dir_path / "model.clf"

    @property
    def json_path(self) -> Path:
        return self.dir_path / "metadata.json"

    def save(self):
        try:
            with open(self.json_path, "w") as f:
                f.write(self.json(indent=4))
            logger.info(f"Saved model: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model {self.name}: {e}")
            return False

    def __str__(self):
        return self.name

    class Config:
        validate_assignment = True


if __name__ == '__main__':
    model = ModelMetadata(name="asd", author="asd", learning_time=0.22,
                          algorithm="KNN Classification",
                          accuracy=0.33, threshold=0.22)
    print(model.dir_path)
    print(model.dict())
