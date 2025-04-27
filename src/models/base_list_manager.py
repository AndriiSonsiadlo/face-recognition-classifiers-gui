import pickle
from abc import ABC
from pathlib import Path
from typing import List, Generic, TypeVar, Optional

from src.utils.logger import AppLogger

T = TypeVar('T')
logger = AppLogger().get_logger(__name__)


class BaseListManager(ABC, Generic[T]):
    """Base class for managing lists of objects"""

    def __init__(self, pickle_path: str):
        self.pickle_path = Path(pickle_path)
        self.list: List[T] = self._load_from_file()

    def _load_from_file(self) -> List[T]:
        """Load list from pickle file"""
        try:
            if not self.pickle_path.exists():
                return []

            with open(self.pickle_path, 'rb') as f:
                data = pickle.load(f)
                return data.list if hasattr(data, 'list') else []
        except (IOError, pickle.PickleError) as e:
            logger.error(f"Failed to load list from {self.pickle_path}: {e}")
            return []

    def save_to_file(self) -> None:
        """Save list to pickle file"""
        try:
            self.pickle_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pickle_path, 'wb') as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
        except IOError as e:
            logger.error(f"Failed to save list: {e}")
            raise

    def add_item(self, item: T) -> None:
        """Add item to list"""
        self.list.append(item)
        self.save_to_file()
        logger.info(f"Added item to list: {item}")

    def remove_item(self, item: T) -> None:
        """Remove item from list"""
        self.list.remove(item)
        self.save_to_file()
        logger.info(f"Removed item from list: {item}")

    def find_by_name(self, name: str) -> Optional[T]:
        """Find item by name attribute"""
        for item in self.list:
            if hasattr(item, 'name') and item.name == name:
                return item
        return None

    def get_all(self) -> List[T]:
        """Get all items"""
        return self.list.copy()

    def is_empty(self) -> bool:
        """Check if list is empty"""
        return len(self.list) == 0

    def clear(self) -> None:
        """Clear all items"""
        self.list.clear()
        self.save_to_file()
