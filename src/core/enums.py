from enum import Enum, IntEnum


class Algorithm(str, Enum):
    KNN = "KNN Classification"
    SVM = "SVM Classification"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class CameraStatus(IntEnum):
    STOPPED = 0
    STARTED = 1
    PAUSED = 2


class PhotoStatus(IntEnum):
    LOADED = 1
    UNLOADED = 0


class AppState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"
