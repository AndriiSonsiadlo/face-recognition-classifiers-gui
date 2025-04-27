class PhotoManager:
    """Centralized photo display management"""

    def __init__(self):
        self.current_index = 0
        self.photos = []

    def load_photos(self, photo_paths: list[str]) -> None:
        self.photos = photo_paths
        self.current_index = 0

    def get_current_photo(self) -> str:
        if not self.photos:
            return self.DEFAULT_USER_IMAGE
        return self.photos[self.current_index]

    def next_photo(self) -> bool:
        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            return True
        return False

    def previous_photo(self) -> bool:
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def get_photo_info(self) -> str:
        if not self.photos:
            return "(0/0)"
        return f"({self.current_index + 1}/{len(self.photos)})"