from typing import Optional
from functools import partial

from kivy.clock import Clock, mainthread

from algorithms.algorithm_loader import AlgorithmWrapper
from core.config import ModelConfig, config
from ui.screens.face_scanner.camera_service import CameraService, CameraError
from utils.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class WebCameraPresenter:
    """
    Presenter in MVP: bridges CameraService (model/service) and the Kivy View.

    Responsibilities:
    - Start/stop camera service
    - Poll frames from CameraService and run algorithm predictions
    - Update the view on the main thread
    - Expose simple API for the View to call
    """

    POLL_INTERVAL = 1.0 / 30.0  # fallback poll interval

    def __init__(self, view, camera_service: CameraService, model_config: Optional[ModelConfig] = None):
        self.view = view
        self.camera_service = camera_service
        self.model_config = model_config
        self.algorithm_wrapper: Optional[AlgorithmWrapper] = None
        self._scheduled_event = None

    def start(self) -> None:
        logger.debug("Presenter start called")
        try:
            if self.model_config:
                self.algorithm_wrapper = AlgorithmWrapper(self.model_config)
                if not self.algorithm_wrapper.load():
                    self.view.show_error("Failed to load ML model")
                    return

            self.camera_service.start()
            # schedule a poller on the Kivy main loop that will pull frames
            self._scheduled_event = Clock.schedule_interval(self._poll_frame, self.POLL_INTERVAL)
            self.view.on_camera_started()
        except CameraError as exc:
            logger.exception("Camera error: %s", exc)
            self.view.show_error(str(exc))
        except Exception:
            logger.exception("Unexpected exception starting presenter")
            self.view.show_error("Unexpected error starting camera")

    def stop(self) -> None:
        logger.debug("Presenter stop called")
        if self._scheduled_event:
            Clock.unschedule(self._scheduled_event)
            self._scheduled_event = None
        self.camera_service.stop()
        self.view.on_camera_stopped()

    def _poll_frame(self, dt):
        ret, frame = self.camera_service.read_now()
        if not ret or frame is None:
            # nothing available right now
            return

        # Run prediction if algorithm available
        try:
            if self.algorithm_wrapper:
                frame, counter, name = self.algorithm_wrapper.predict_webcam(frame)
                self._handle_prediction(counter, name)
        except Exception:
            logger.exception("Error running prediction")

        # Pass the frame to view for rendering on the main thread
        self.view.render_frame(frame)

    def _handle_prediction(self, counter: int, name: str) -> None:
        try:
            if counter >= config.person.DEFAULT_COUNT_FRAME and name != config.ui.TEXTS["unknown"]:
                self.view.set_identification(name)
                # Stop auto capture
                self.stop()
            else:
                self.view.reset_identification()
        except Exception:
            logger.exception("Error updating view with prediction")

