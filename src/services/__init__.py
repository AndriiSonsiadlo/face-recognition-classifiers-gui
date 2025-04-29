from .camera_service import CameraService
from .model_service import ModelService
from .person_service import PersonService

person_service = PersonService()
model_service = ModelService()
camera_service = CameraService()

__all__ = ['person_service', 'model_service', 'camera_service']
