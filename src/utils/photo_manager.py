from typing import List, Optional
from pathlib import Path
class PhotoManager:
    """Centralized photo display and management."""
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

    def __init__(self, photos: Optional[List[str]] = None):
        """Initialize PhotoManager.

        Args:
            photos: List of photo paths to load initially
        """
        self.photos: List[str] = photos or []
        self.current_index: int = 0

    def load_photos(self, photo_paths: List[str]) -> int:
        """Load and validate photos.

        Args:
            photo_paths: List of photo file paths

        Returns:
            Number of valid photos loaded
        """
        valid_photos = [
            p for p in photo_paths
            if self._is_valid_image(p)
        ]
        self.photos = valid_photos
        self.current_index = 0
        return len(valid_photos)

    def get_current(self) -> Optional[str]:
        """Get current photo path.

        Returns:
            Current photo path or None if empty
        """
        if not self.photos or self.current_index >= len(self.photos):
            return None
        return self.photos[self.current_index]

    def next(self) -> bool:
        """Move to next photo.

        Returns:
            True if moved, False if at end
        """
        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            return True
        return False

    def previous(self) -> bool:
        """Move to previous photo.

        Returns:
            True if moved, False if at start
        """
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def remove_current(self) -> bool:
        """Remove current photo from list.

        Returns:
            True if removed, False if list empty
        """
        if not self.photos:
            return False

        self.photos.pop(self.current_index)

        # Adjust index if needed
        if self.current_index >= len(self.photos) and self.photos:
            self.current_index = len(self.photos) - 1

        return True

    def add_photos(self, new_photos: List[str]) -> int:
        """Add photos to existing list.

        Args:
            new_photos: List of photo paths to add

        Returns:
            Number of photos added
        """
        valid = [p for p in new_photos if self._is_valid_image(p)]
        self.photos.extend(valid)
        return len(valid)

    def get_info(self) -> str:
        """Get photo count info string.

        Returns:
            Format: "(current/total)" or "(0/0)" if empty
        """
        if not self.photos:
            return "(0/0)"
        return f"({self.current_index + 1}/{len(self.photos)})"

    def get_all(self) -> List[str]:
        """Get all photo paths.

        Returns:
            Copy of photos list
        """
        return self.photos.copy()

    def is_empty(self) -> bool:
        """Check if photo list is empty.

        Returns:
            True if empty
        """
        return len(self.photos) == 0

    def clear(self) -> None:
        """Clear all photos."""
        self.photos.clear()
        self.current_index = 0

    @staticmethod
    def _is_valid_image(path: str) -> bool:
        """Validate image file exists and has correct extension.

        Args:
            path: File path to validate

        Returns:
            True if valid image file
        """
        try:
            p = Path(path)
            return (
                p.exists() and
                p.is_file() and
                p.suffix.lower() in PhotoManager.SUPPORTED_EXTENSIONS
            )
        except (OSError, ValueError):
            return False