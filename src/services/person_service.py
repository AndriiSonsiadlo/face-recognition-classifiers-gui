import shutil
from pathlib import Path
from typing import List, Optional

from core.logger import AppLogger
from models.person.person_metadata import PersonMetadata, ImageValidator
from models.person.person_registry import PersonRegistry

logger = AppLogger().get_logger(__name__)


class PersonService:
    def __init__(self, registry: Optional[PersonRegistry] = None):
        self.registry = registry or PersonRegistry()

    def create_person(
            self, person: PersonMetadata, photo_paths: List[str], **kwargs
    ) -> Optional[PersonMetadata]:
        try:
            photo_paths: List[Path] = ImageValidator.validate_images(photo_paths)
            if not photo_paths:
                logger.warning(f"No valid photos for person {person.name}")

            if self.registry.add(person):
                logger.info(f"Created person: {person.name}")

                for i, photo_path in enumerate(photo_paths, start=1):
                    photo_path = Path(photo_path)
                    dst = person.photos_path / f"{i}{photo_path.suffix}"
                    shutil.copy2(str(photo_path), str(dst))
                    logger.info(f"Copied photo to: {dst}")

                person.save()
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

    def get_persons_with_photos(self, min_photos: int = 1) -> List[PersonMetadata]:
        return self.registry.filter(lambda p: len(p.photo_paths) >= min_photos)

    def search_persons(self, query: str = None) -> List[PersonMetadata]:
        if not query:
            return self.registry.get_all()
        return self.registry.search(query)

    def update_person(
            self, original_name: str, new_name: Optional[str] = None, **kwargs
    ) -> Optional[PersonMetadata]:
        try:
            name_to_use = new_name if new_name else original_name

            person = self.registry.get(original_name)
            if not person:
                logger.error(f"Person not found: {original_name}")
                return None

            self.registry.update(original_name, name_to_use, **kwargs)

            if new_name and new_name != original_name:
                try:
                    from core import config
                    old_path = config.paths.PERSON_DATA_DIR / original_name
                    new_path = config.paths.PERSON_DATA_DIR / new_name

                    if old_path.exists() and not new_path.exists():
                        old_path.rename(new_path)
                        logger.info(f"Renamed person directory: {original_name} -> {new_name}")
                except Exception as e:
                    logger.exception(f"Error renaming person directory: {e}")
                    raise

            person = self.registry.get(name_to_use)
            if person:
                person.photos_path.mkdir(parents=True, exist_ok=True)

                person.save()
                logger.info(f"Updated person: {name_to_use}")
                return person
            else:
                return None

        except Exception as e:
            logger.exception(f"Error updating person {original_name}: {e}")
            return None

    def delete_person(self, name: str) -> bool:
        try:
            success = self.registry.delete(name)
            if success:
                logger.info(f"Deleted person: {name}")
            return success
        except Exception as e:
            logger.exception(f"Error deleting person {name}: {e}")
            return False

    def add_photos_to_person(self, name: str, photo_paths: List[str]) -> List[str]:
        try:
            person = self.registry.get(name)
            if not person:
                logger.warning(f"Person '{name}' not found")
                return []

            valid_photos = ImageValidator.validate_images(photo_paths)
            if not valid_photos:
                logger.warning(f"No valid photos to add for {name}")
                return []

            person.photos_path.mkdir(parents=True, exist_ok=True)

            existing_photos = list(person.photos_path.glob("*"))
            photo_count = len(existing_photos)

            added_photos = []
            for photo_path in valid_photos:
                try:
                    src = Path(photo_path)
                    if not src.exists():
                        logger.warning(f"Source photo not found: {photo_path}")
                        continue

                    photo_count += 1
                    dst = person.photos_path / f"{photo_count}{src.suffix}"

                    shutil.copy2(str(src), str(dst))
                    added_photos.append(str(dst))
                    logger.info(f"Added photo to {name}: {dst}")

                except Exception as e:
                    logger.exception(f"Error copying photo {photo_path}: {e}")
                    continue

            person.save()

            logger.info(f"Added {len(added_photos)} photos to {name}")
            return added_photos

        except Exception as e:
            logger.exception(f"Error adding photos to {name}: {e}")
            return []

    def remove_photo_from_person(self, name: str, photo_path: str) -> bool:
        try:
            person = self.registry.get(name)
            if not person:
                logger.warning(f"Person '{name}' not found")
                return False

            photo_p = Path(photo_path)
            if not photo_p.exists():
                logger.warning(f"Photo not found: {photo_path}")
                return False

            photo_p.unlink()
            logger.info(f"Deleted photo from disk: {photo_path}")

            person.save()

            return True

        except Exception as e:
            logger.exception(f"Error removing photo from {name}: {e}")
            return False

    def refresh(self) -> None:
        try:
            self.registry.refresh()
            logger.info("Refreshed person registry from disk")
        except Exception as e:
            logger.exception("Error refreshing person registry")
