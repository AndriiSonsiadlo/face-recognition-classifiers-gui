from enum import Enum, IntEnum


class Algorithm(str, Enum):
    """Available ML algorithms."""
    KNN = "KNN Classification"
    SVM = "SVM Classification"


class Gender(str, Enum):
    """Gender options."""
    MALE = "Male"
    FEMALE = "Female"


class CameraStatus(IntEnum):
    """Camera operational status."""
    STOPPED = 0
    STARTED = 1
    PAUSED = 2


class PhotoStatus(IntEnum):
    """Photo loading status."""
    LOADED = 0b1
    UNLOADED = 0b0


class AppState(str, Enum):
    """Application states."""
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"
