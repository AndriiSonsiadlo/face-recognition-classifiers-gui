from pathlib import Path
from typing import Optional, Tuple

from algorithms import AlgorithmFactory
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata
from models.prediction import Prediction
from services import person_service, model_service, camera_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class FaceScannerPresenter(BasePresenter):
    """Presenter for Face Scanner screen."""

    def __init__(self, view):
        super().__init__(view)
        self.algorithm = None

    def start(self) -> None:
        """Start presenter (load initial data)."""
        try:
            model_service.refresh()
            person_service.refresh()
            logger.info("FaceScannerPresenter started")
        except Exception as e:
            logger.exception("Error starting FaceScannerPresenter")
            self.show_error(str(e))

    def stop(self) -> None:
        self.stop_camera()

    def start_camera(self, camera_port: int, model: ModelMetadata) -> bool:
        try:
            if not model:
                self.show_error(f"Model '{model}' not found")
                return False

            self.algorithm = AlgorithmFactory.create(model)
            if not self.algorithm.load_model():
                self.show_error("Failed to load model")
                self.algorithm = None
                return False

            camera_service.start(camera_port)
            self.view.ids.camera.on_camera_started()
            logger.info(f"Camera started on port {camera_port}")
            return True

        except Exception as e:
            logger.exception("Failed to start camera")
            self.show_error(str(e))
            self.algorithm = None
            return False

    def stop_camera(self) -> None:
        try:
            camera_service.stop()
            self.algorithm = None
            self.view.on_camera_stopped()
            logger.info("Camera stopped")
        except Exception as e:
            logger.exception("Error stopping camera")

    def process_frame(self, frame) -> Optional[Prediction]:
        if not self.algorithm or frame is None:
            return None

        try:
            name, counter = self.algorithm.predict_webcam(frame)
            return Prediction(name=name, confidence=0.0, counter=counter, frame=frame)
        except Exception as e:
            logger.exception("Error processing frame")
            return None

    def load_photo(self, image_path: str) -> Optional[Tuple]:
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            if not self.algorithm:
                raise RuntimeError("Algorithm not loaded")

            frame, name = self.algorithm.predict_from_image(image_path)
            return frame, name

        except Exception as e:
            logger.exception(f"Failed to load photo: {image_path}")
            self.show_error(str(e))
            return None

    def show_person_info(self, name: str) -> bool:
        try:
            persons = person_service.search_persons(name)
            if not persons:
                self.view.show_warning(f"Person '{name}' not found")
                return False

            self.view.show_person_info(persons[0])
            return True

        except Exception as e:
            logger.exception("Error showing person info")
            self.show_error(str(e))
            return False

    def get_available_models(self):
        try:
            models = model_service.get_all_models()
            return [m.name for m in models]
        except Exception as e:
            logger.exception("Error getting available models")
            return []

    def get_person_count(self) -> int:
        try:
            return len(person_service.get_all_persons())
        except Exception as e:
            logger.exception("Error getting person count")
            return 0

    def get_model_info(self, model_name: str) -> Optional[dict]:
        try:
            model = model_service.get_model(model_name)
            if not model:
                return None

            return {
                'name': model.name,
                'algorithm': model.algorithm.value,
                'accuracy': model.accuracy,
                'train_count': model.count_train_Y,
                'test_count': model.count_test_Y,
            }
        except Exception as e:
            logger.exception(f"Error getting model info for {model_name}")
            return None
