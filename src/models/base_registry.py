from abc import ABC
from pathlib import Path
from typing import List, Callable, Generic, TypeVar

from core import AppLogger

logger = AppLogger().get_logger(__name__)

T = TypeVar('T')


class BaseRegistry(ABC, Generic[T]):
    def __init__(self, root_dir: Path, baseModel):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

        self.items: List[baseModel] = []
        self.baseModel = baseModel
        self.refresh()

    def refresh(self) -> None:
        """Scan directory structure and rebuild in-memory list."""
        self.items.clear()

        for dirpath in self.root_dir.iterdir():
            if not dirpath.is_dir() or dirpath.name == 'temp':
                continue

            metadata_file = dirpath / 'metadata.json'
            if not metadata_file.exists():
                continue

            try:
                self.items.append(self.baseModel.parse_file(metadata_file))
            except Exception as e:
                logger.info(f"Failed to load person metadata from {metadata_file}: {e}")

        logger.info(f"Loaded {len(self.items)} persons")

    def add(self, item) -> bool:
        if self.exists(item.name):
            logger.warning(f"Person {item.name} already exists")
            return False

        try:
            item.dir_path.mkdir(parents=True, exist_ok=True)
            item.save()

            self.items.append(item)
            logger.info(f"Added item: {item.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add item {item.name}: {e}")
            return False

    def get(self, name: str):
        for item in self.items:
            if item.name.lower() == name.lower():
                return item
        return None

    def get_count(self) -> int:
        return len(self.items)

    def get_all(self):
        return self.items.copy()

    def delete(self, name: str) -> bool:
        import shutil

        item = self.get(name)
        if not item:
            logger.warning(f"Person {name} not found")
            return False

        try:
            if item.dir_path.exists():
                shutil.rmtree(item.dir_path)

            self.items.remove(item)
            logger.info(f"Deleted item: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete item {name}: {e}")
            return False

    def filter(self, lmbd: Callable):
        return list(filter(lmbd, self.items))

    def search(self, query: str):
        query_lower = query.lower()
        return [
            p for p in self.items
            if query_lower in p.name.lower()
        ]

    def exists(self, name: str) -> bool:
        return self.get(name) is not None

    def update(self, name: str, **kwargs) -> bool:
        item = self.get(name)
        if not item:
            return False

        errors = []
        for field, value in kwargs.items():
            try:
                setattr(item, field, value)
            except Exception as e:
                errors.append(e)

        if not errors:
            return item.save()

        logger.error(f"Failed to update fields for item {item.name}:")
        for err in errors:
            logger.error(err)

        return False
