from pathlib import Path
from typing import Optional

from kivy.clock import Clock, mainthread

from algorithms import AlgorithmFactory
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata

logger = AppLogger().get_logger(__name__)


class WebCameraPresenter:
    POLL_INTERVAL = 1.0 / 30.0  # 30 FPS

    def __init__(self, view, camera_svc):
        self.view = view
        self.camera_service = camera_svc
        self.algorithm = None
        self._poll_event = None
        self._is_running = False

    def start(self) -> None:
        logger.info("WebCameraPresenter started")

    def stop(self) -> None:
        try:
            self._stop_camera_impl()
            logger.info("WebCameraPresenter stopped")
        except Exception as e:
            logger.exception("Error stopping WebCameraPresenter")

    def toggle_camera(self, camera_port: int, model: Optional[ModelMetadata]) -> None:
        try:
            if self._is_running:
                self._stop_camera_impl()
            else:
                self._start_camera_impl(camera_port, model)
        except Exception as e:
            logger.exception("Error toggling camera")
            self.view.on_camera_error(str(e))

    def _start_camera_impl(self, camera_port: int, model: Optional[ModelMetadata]) -> None:
        try:
            if not model:
                raise ValueError("No model selected")

            if camera_port is None:
                raise ValueError("No camera port selected")

            self._load_algorithm(model)
            if not self.algorithm:
                raise RuntimeError("Failed to load algorithm")

            self.camera_service.start(camera_port)
            self._is_running = True

            if self._poll_event:
                Clock.unschedule(self._poll_event)
            self._poll_event = Clock.schedule_interval(
                self._poll_frame_impl,
                self.POLL_INTERVAL
            )

            self.view.on_camera_started()
            logger.info(f"Camera started on port {camera_port}")

        except Exception as e:
            logger.exception("Error starting camera")
            self._is_running = False
            self.view.on_camera_error(str(e))

    def _stop_camera_impl(self) -> None:
        try:
            if self._poll_event:
                Clock.unschedule(self._poll_event)
                self._poll_event = None

            self.camera_service.stop()

            self.algorithm = None
            self._is_running = False

            self.view.on_camera_stopped()
            logger.info("Camera stopped")

        except Exception as e:
            logger.exception("Error stopping camera")
            self.view.on_camera_error(str(e))

    def _poll_frame_impl(self, dt) -> None:
        try:
            if not self._is_running or not self.algorithm:
                return

            ret, frame = self.camera_service.read_now()
            if not ret or frame is None:
                return

            self.last_frame = frame.copy()

            rgb_frame = frame[:, :, ::-1]
            try:
                annotated, counter, name = self.algorithm.predict_webcam(rgb_frame)

                prediction_data = {
                    'frame': annotated,
                    'name': name,
                    'counter': counter,
                    'confidence': 0.0
                }

                self.view.on_frame_received(prediction_data)

            except Exception as e:
                logger.exception("Error running prediction")

        except Exception as e:
            logger.exception("Error in frame polling")

    def _load_algorithm(self, model: ModelMetadata) -> bool:
        try:
            if not model:
                raise ValueError("Model is None")

            self.algorithm = AlgorithmFactory.create(model)

            if not self.algorithm.load_model():
                logger.error(f"Failed to load model file: {model.clf_path}")
                self.algorithm = None
                return False

            logger.info(f"Algorithm loaded: {model.name}")
            return True

        except Exception as e:
            logger.exception(f"Error loading algorithm for {model.name if model else 'Unknown'}")
            self.algorithm = None
            return False

    def load_photo_from_file(self, model) -> None:
        self._load_photo_threaded(model)
        # thread = threading.Thread(target=self._load_photo_threaded, daemon=True)
        # thread.start()

    @mainthread
    def _load_photo_threaded(self, model) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()

            photo_paths = filedialog.askopenfilenames(
                filetypes=[("Image files", "*.jpeg *.jpg *.png *.bmp")]
            )

            if not photo_paths:
                return

            image_path = str(photo_paths[0])

            self._load_algorithm(model)
            result = self._process_image_impl(image_path)

            if result:
                frame, name = result
                self.view.on_photo_loaded(frame, name)
            else:
                self.view.on_photo_error("Failed to process image")

            try:
                root.lift()
            except:
                pass

        except Exception as e:
            logger.exception("Error in photo loading thread")
            self.view.on_photo_error(str(e))

    def _process_image_impl(self, image_path: str) -> Optional[tuple]:
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            if not self.algorithm:
                raise RuntimeError("Algorithm not loaded. Start camera first or select a model.")

            frame, name = self.algorithm.predict_from_image(image_path)

            logger.info(f"Image processed: {image_path} -> {name}")
            return frame, name

        except Exception as e:
            logger.exception(f"Error processing image: {image_path}")
            return None

    def is_camera_running(self) -> bool:
        return self._is_running

    def is_algorithm_loaded(self) -> bool:
        return self.algorithm is not None
