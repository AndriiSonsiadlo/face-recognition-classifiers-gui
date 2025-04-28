import os
from pathlib import Path
from typing import Set, List, Dict

from pydantic import BaseModel, validator


class PathConfig(BaseModel):
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    SRC_DIR: Path = BASE_DIR / "src"

    PERSON_DATA_DIR: Path = BASE_DIR / "person_data"
    MODEL_DATA_DIR: Path = BASE_DIR / "model_data"
    TEMP_DIR: Path = BASE_DIR / "temp"
    STATS_DIR: Path = BASE_DIR / "statistics"
    ASSETS_DIR: Path = SRC_DIR / "assets"
    LOGS_DIR: Path = BASE_DIR / "logs"

    class Config:
        arbitrary_types_allowed = True


# ============================================================
# UI Configuration
# ============================================================

class UIConfig(BaseModel):
    TEXT_COLORS: Dict[str, tuple] = {
        "header": (0 / 255, 102 / 255, 178 / 255, 1),
        "normal": (0.2, 0.2, 0.2, 1),
    }

    TEXTS: Dict[str, str] = {
        "unnamed": "Unnamed",
        "unknown": "Unknown",
        "learning": "Learning...",
        "train_model": "Train model",
        "completed": "Completed",
        "no_elements": "No elements",
        "start_webcam": "Turn on",
        "stop_webcam": "Turn off",
        "load_photo": "Load Photo",
        "clear_photo": "Clear Photo",
    }


# ============================================================
# Person Configuration
# ============================================================

class PersonConfig(BaseModel):
    ALLOWED_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg", "bmp", "tiff"}
    MAX_PHOTO_SIZE_MB = 50
    DEFAULT_COUNT_PHOTOS: int = 1
    DEFAULT_COUNT_FRAME: int = 5
    MIN_PHOTOS_FOR_TRAINING: int = 1

    def validate_image(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower().lstrip('.')
        return ext in self.ALLOWED_EXTENSIONS


class ModelConfig(BaseModel):
    DEFAULT_THRESHOLD: float = 0.5
    DEFAULT_N_NEIGHBORS: int = 5
    DEFAULT_WEIGHT: str = "distance"
    DEFAULT_GAMMA: str = "scale"

    ALGORITHM_KNN: str = "KNN Classification"
    ALGORITHM_SVM: str = "SVM Classification"


class StatisticsConfig(BaseModel):
    FILE_STATS_PLOT: Path = PathConfig().STATS_DIR / "plot.png"
    FILE_STATS_CSV: Path = PathConfig().STATS_DIR / "basic_data.csv"
    FILE_RESULT_PLOT: Path = PathConfig().STATS_DIR / "result.png"


class ImageAssetConfig(BaseModel):
    CAMERA_DISABLED_IMAGE: Path = PathConfig().ASSETS_DIR / "images" / "camera_off_2.png"
    DEFAULT_USER_IMAGE: Path = PathConfig().ASSETS_DIR / "images" / "default-user.png"


class MainConfig(BaseModel):
    paths: PathConfig = PathConfig()
    ui: UIConfig = UIConfig()
    model: ModelConfig = ModelConfig()
    person: PersonConfig = PersonConfig()
    stats: StatisticsConfig = StatisticsConfig()
    images: ImageAssetConfig = ImageAssetConfig()

    CAMERA_PORTS: List[str] = ["Port 0", "Port 1", "Port 2", "Port 3", "Port 4"]

    @validator("paths", pre=False, always=True)
    def create_directories(cls, v: PathConfig, values):
        """
        Ensures main directories exist.
        """
        os.makedirs(v.PERSON_DATA_DIR, exist_ok=True)
        os.makedirs(v.MODEL_DATA_DIR, exist_ok=True)
        os.makedirs(v.TEMP_DIR, exist_ok=True)
        os.makedirs(v.STATS_DIR, exist_ok=True)
        os.makedirs(v.LOGS_DIR, exist_ok=True)

        return v

    def get_person_path(self, person_name: str) -> Path:
        return self.paths.PERSON_DATA_DIR / person_name

    def get_model_path(self, model_name: str) -> Path:
        return self.paths.MODEL_DATA_DIR / model_name

    class Config:
        arbitrary_types_allowed = True


config = MainConfig()
