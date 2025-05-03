import os
from pathlib import Path
from typing import Optional

from core import AppLogger, config
from models.base_registry import BaseRegistry
from models.person.person_metadata import PersonMetadata

logger = AppLogger().get_logger(__name__)


class PersonRegistry(BaseRegistry):
    """Registry for managing persons and their data."""

    def __init__(self, root_dir: Optional[Path] = None):
        super().__init__(root_dir or config.paths.PERSON_DATA_DIR, PersonMetadata)

    def add(self, item) -> bool:
        success = super().add(item)
        if success:
            item.photos_path.mkdir(exist_ok=True)
        return success

    def update(self, name, new_name, **kwargs) -> None:
        kwargs['name'] = new_name
        super().update(name, **kwargs)
        if name != new_name:
            os.rename(
                config.paths.PERSON_DATA_DIR / name,
                config.paths.PERSON_DATA_DIR / new_name
            )


if __name__ == '__main__':
    pr = PersonRegistry()
