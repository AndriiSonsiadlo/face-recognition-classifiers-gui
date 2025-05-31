from pathlib import Path
from typing import List, Optional


class PhotoManager:
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

    def __init__(self, photos: Optional[List[str]] = None):
        self.photos: List[str] = photos or []
        self.current_index: int = 0

    def load_photos(self, photo_paths: List[str]) -> int:
        valid_photos = [
            p for p in photo_paths
            if self._is_valid_image(p)
        ]
        self.photos = valid_photos
        self.current_index = 0
        return len(valid_photos)

    def get_current(self) -> Optional[str]:
        if not self.photos or self.current_index >= len(self.photos):
            return None
        return self.photos[self.current_index]

    def next(self) -> bool:
        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            return True
        return False

    def previous(self) -> bool:
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def remove_current(self) -> bool:
        if not self.photos:
            return False

        self.photos.pop(self.current_index)

        if self.current_index >= len(self.photos) and self.photos:
            self.current_index = len(self.photos) - 1

        return True

    def add_photos(self, new_photos: List[str]) -> int:
        valid = [p for p in new_photos if self._is_valid_image(p)]
        self.photos.extend(valid)
        return len(valid)

    def get_info(self) -> str:
        if not self.photos:
            return "(0/0)"
        return f"({self.current_index + 1}/{len(self.photos)})"

    def get_all(self) -> List[str]:
        return self.photos.copy()

    def is_empty(self) -> bool:
        return len(self.photos) == 0

    def clear(self) -> None:
        self.photos.clear()
        self.current_index = 0

    @staticmethod
    def _is_valid_image(path: str) -> bool:
        try:
            p = Path(path)
            return (
                    p.exists() and
                    p.is_file() and
                    p.suffix.lower() in PhotoManager.SUPPORTED_EXTENSIONS
            )
        except (OSError, ValueError):
            return False
