import shutil
from pathlib import Path
from typing import List, Optional

from core.logger import AppLogger
from models.person.person_metadata import PersonMetadata, ImageValidator
from models.person.person_registry import PersonRegistry

logger = AppLogger().get_logger(__name__)


class PersonService:
    """Business logic for persons."""

    def __init__(self, registry: Optional[PersonRegistry] = None):
        """Initialize PersonService.

        Args:
            registry: PersonRegistry instance
        """
        self.registry = registry or PersonRegistry()

    def create_person(
            self, person: PersonMetadata, photo_paths: List[str], **params
    ) -> Optional[PersonMetadata]:
        try:
            photo_paths: List[Path] = ImageValidator.validate_images(photo_paths)
            if not photo_paths:
                logger.warning(f"No valid photos for person {person.name}")

            if self.registry.add(person):
                logger.info(f"Created person: {person.name}")
                for i, photo_path in enumerate(photo_paths, start=1):
                    photo_path = Path(photo_path)
                    shutil.copy(photo_path, person.photos_path / f"{i}{photo_path.suffix}")
                return person
            else:
                return None

        except Exception as e:
            logger.exception(f"Error creating person {person.name}: {e}")
            raise

    def get_person(self, name: str) -> Optional[PersonMetadata]:
        return self.registry.get(name)

    def get_all_persons(self) -> List[PersonMetadata]:
        return self.registry.get_all()

    def get_persons_with_photos(
            self, min_photos: int = 1
    ) -> List[PersonMetadata]:
        return self.registry.filter(lambda p: len(p.photo_paths) >= min_photos)

    def search_persons(self, query: str = None) -> List[PersonMetadata]:
        if not query:
            return self.registry.get_all()
        return self.registry.search(query)

    def update_person(
            self,
            name: str,
            new_name: Optional[str] = None,
            photos: Optional[List[Path]] = None,
            **kwargs
    ) -> Optional[PersonMetadata]:
        try:
            self.registry.update(name, new_name, **kwargs)

            person = self.registry.get(new_name)
            if photos is not None:
                pass


        except Exception as e:
            logger.exception(f"Error updating person {name}: {e}")
            return None

    def delete_person(self, name: str) -> bool:
        """Delete person and associated files.

        Args:
            name: Person name

        Returns:
            True if successful
        """
        try:
            success = self.registry.delete(name)
            if success:
                logger.info(f"Deleted person: {name}")
            return success
        except Exception as e:
            logger.exception(f"Error deleting person {name}: {e}")
            return False

    def add_photos_to_person(
            self,
            name: str,
            photo_paths: List[str]
    ) -> List[str]:
        """Add photos to existing person.

        Args:
            name: Person name
            photo_paths: List of photo paths to add

        Returns:
            List of added photo paths
        """
        try:
            person = self.registry.get(name)
            if not person:
                logger.warning(f"Person '{name}' not found")
                return []

            valid_photos = ImageValidator.validate_images(photo_paths)
            new_photos = [p for p in valid_photos if p not in person.photo_paths]

            person.photo_paths.extend(new_photos)
            self.registry.save_person(person)

            logger.info(f"Added {len(new_photos)} photos to {name}")
            return new_photos

        except Exception as e:
            logger.exception(f"Error adding photos to {name}: {e}")
            return []

    def remove_photo_from_person(
            self,
            name: str,
            photo_path: str
    ) -> bool:
        """Remove photo from person.

        Args:
            name: Person name
            photo_path: Photo path to remove

        Returns:
            True if removed
        """
        try:
            person = self.registry.get(name)
            if not person or photo_path not in person.photo_paths:
                return False

            person.photo_paths.remove(photo_path)
            self.registry.save_person(person)

            logger.info(f"Removed photo from {name}")
            return True

        except Exception as e:
            logger.exception(f"Error removing photo from {name}: {e}")
            return False

    def refresh(self) -> None:
        """Refresh registry from disk."""
        self.registry.refresh()
        logger.info("Refreshed person registry")
