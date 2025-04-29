from pathlib import Path
from typing import Optional

from core import config, AppLogger
from models.base_registry import BaseRegistry
from models.model.model_metadata import ModelMetadata

logger = AppLogger().get_logger(__name__)


class ModelRegistry(BaseRegistry):
    """Registry for managing models and their data."""

    def __init__(self, root_dir: Optional[Path] = None):
        super().__init__(root_dir or config.paths.MODEL_DATA_DIR, ModelMetadata)


if __name__ == '__main__':
    mr = ModelRegistry()
    mr.add(ModelMetadata(name="Algorithm_2", learning_time=4, algorithm="KNN Classification",
                         accuracy=0.2, threshold=0.5))
