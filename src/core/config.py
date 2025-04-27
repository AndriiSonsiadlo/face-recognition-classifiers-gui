import os
from pathlib import Path
from typing import Set, List, Dict

from pydantic import BaseModel, validator


# ============================================================
# Path Configuration
# ============================================================

class PathConfig(BaseModel):
    BASE_DIR: Path = Path(__file__).parent.parent
    SRC_DIR: Path = BASE_DIR.parent

    PERSON_DATA_DIR: Path = BASE_DIR / "person_data"
    MODEL_DATA_DIR: Path = BASE_DIR / "model_data"
    TEMP_DIR: Path = BASE_DIR / "temp"
    STATS_DIR: Path = BASE_DIR / "statistics"
    ASSETS_DIR: Path = SRC_DIR / "assets"

    # file_person_list_pkl: str = "person_list.pkl"
    # filename_model_list_pkl: str = "model_list.pkl"

    # ============================================================
    # Person Configuration
    # ============================================================

    def get_dir_person_data(self, person_name: str) -> Path:
        return self.PERSON_DATA_DIR / person_name

    def get_dir_person_photo(self, person_name: str) -> Path:
        return self.get_dir_person_data(person_name) / "photos"

    def get_file_person_metadata(self, person_name: str) -> Path:
        return self.get_dir_person_data(person_name) / "metadata.json"

    # ============================================================
    # Model Configuration
    # ============================================================

    def get_dir_model_data(self, model_name: str) -> Path:
        return self.MODEL_DATA_DIR / model_name

    def get_file_model_metadata(self, model_name: str) -> Path:
        return self.get_dir_model_data(model_name) / "metadata.json"

    def get_file_model(self, model_name: str) -> Path:
        return self.get_dir_model_data(model_name) / "model.clf"


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
    DEFAULT_COUNT_PHOTOS: int = 1
    DEFAULT_COUNT_FRAME: int = 5

    def validate_image(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower().lstrip('.')
        return ext in self.ALLOWED_EXTENSIONS


# ============================================================
# Machine Learning Model Configuration
# ============================================================

class ModelConfig(BaseModel):
    DEFAULT_THRESHOLD: float = 0.5

    ALGORITHM_KNN: str = "KNN Classification"
    ALGORITHM_SVM: str = "SVM Classification"


# ============================================================
# Statistics Configuration
# ============================================================

class StatisticsConfig(BaseModel):
    FILE_STATS_PLOT: Path = PathConfig().STATS_DIR / "plot.png"
    FILE_STATS_CSV: Path = PathConfig().STATS_DIR / "basic_data.csv"
    FILE_RESULT_PLOT: Path = PathConfig().STATS_DIR / "result.png"


# ============================================================
# Image Assets Configuration
# ============================================================

class ImageAssetConfig(BaseModel):
    CAMERA_DISABLED_IMAGE: Path = PathConfig().ASSETS_DIR / "camera_off_2.png"
    DEFAULT_USER_IMAGE: Path = PathConfig().ASSETS_DIR / "default-user.png"


# ============================================================
# Main Aggregated Configuration
# ============================================================

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

        return v

    def get_person_path(self, person_name: str) -> Path:
        return self.paths.PERSON_DATA_DIR / person_name

    def get_model_path(self, model_name: str) -> Path:
        return self.paths.MODEL_DATA_DIR / model_name


config = MainConfig()
