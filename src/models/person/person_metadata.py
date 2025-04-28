from datetime import datetime
from pathlib import Path
from typing import List

from pydantic import BaseModel, NonNegativeInt

from core import config, AppLogger
from src.core.enums import Gender

logger = AppLogger().get_logger(__name__)


class PersonMetadata(BaseModel):
    name: str
    gender: Gender
    age: NonNegativeInt
    nationality: str = ""
    details: str = ""
    contact_phone: str = "N/A"

    created_at: datetime = datetime.now()

    @property
    def photo_paths(self) -> List[Path]:
        photos = []
        for filename in self.photos_path.iterdir():
            if not filename.is_file():
                continue

            filepath = self.photos_path / filename
            if ImageValidator.validate_image(filepath):
                photos.append(filepath)
        return photos

    @property
    def created_format(self) -> str:
        return self.created_at.strftime("%d %b %Y at %H:%M")

    @property
    def dir_path(self) -> Path:
        return config.paths.PERSON_DATA_DIR / self.name

    @property
    def photos_path(self) -> Path:
        return self.dir_path / "photos"

    @property
    def json_path(self) -> Path:
        return self.dir_path / "metadata.json"

    def save(self):
        try:
            with open(self.json_path, "w") as f:
                f.write(self.json(indent=4))
            logger.info(f"Saved person metadata: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save person metadata {self.name}: {e}")
            return False

    class Config:
        validate_assignment = True


class ImageValidator:
    """Validates image files."""

    @staticmethod
    def validate_image(file_path: Path) -> bool:
        try:
            if not file_path.exists() or not file_path.is_file():
                return False

            if file_path.suffix.lower() not in config.person.ALLOWED_EXTENSIONS:
                return False

            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > config.person.MAX_PHOTO_SIZE_MB:
                return False

            return True
        except (OSError, ValueError):
            return False

    @classmethod
    def validate_images(cls, photo_paths):
        return [p for p in photo_paths if cls.validate_image(p)]
