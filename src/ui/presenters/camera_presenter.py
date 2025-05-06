import threading
from pathlib import Path
from typing import Optional

from kivy.clock import Clock

from algorithms import AlgorithmFactory
from algorithms.algorithm_wrapper import AlgorithmWrapper
from core.config import ModelConfig, config
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata
from services.camera_service import CameraService, CameraError

logger = AppLogger().get_logger(__name__)


class WebCameraPresenter:
    """Presenter for camera and face recognition operations.

    Responsibilities:
    - Load and manage ML algorithm
    - Control camera start/stop
    - Process frames and run predictions
    - Photo loading and processing
    - Callbacks to view
    """

    POLL_INTERVAL = 1.0 / 30.0  # 30 FPS

    def __init__(self, view, camera_svc):
        self.view = view
        self.camera_service = camera_svc
        self.algorithm = None
        self._poll_event = None
        self._is_running = False

    def start(self) -> None:
        """Initialize presenter (called on screen init)."""
        logger.info("WebCameraPresenter started")

    def stop(self) -> None:
        """Stop presenter (called on screen leave)."""
        try:
            self._stop_camera_impl()
            logger.info("WebCameraPresenter stopped")
        except Exception as e:
            logger.exception("Error stopping WebCameraPresenter")

    # ============================================================
    # Camera Control
    # ============================================================

    def toggle_camera(self, camera_port: int, model: Optional[ModelMetadata]) -> None:
        """Toggle camera on/off.

        Args:
            camera_port: Camera port selection (e.g., "Port 0")
            model: ModelMetadata to load algorithm from
        """
        try:
            if self._is_running:
                self._stop_camera_impl()
            else:
                self._start_camera_impl(camera_port, model)
        except Exception as e:
            logger.exception("Error toggling camera")
            self.view.on_camera_error(str(e))

    def _start_camera_impl(self, camera_port: int, model: Optional[ModelMetadata]) -> None:
        """Internal camera start implementation.

        Args:
            camera_port: Camera port string
            model: Model to load
        """
        try:
            # if not model:
            #     raise ValueError("No model selected")

            # Extract port number from "Port 0" format
            if camera_port is None:
                raise ValueError("No camera port selected")

            # Load algorithm
            # self._load_algorithm(model)
            # if not self.algorithm:
            #     pass
                # raise RuntimeError("Failed to load algorithm")

            # Start camera service
            self.camera_service.start(camera_port)
            self._is_running = True

            # Schedule frame polling on Kivy main thread
            if self._poll_event:
                Clock.unschedule(self._poll_event)
            self._poll_event = Clock.schedule_interval(
                self._poll_frame_impl,
                self.POLL_INTERVAL
            )

            # Notify view
            self.view.on_camera_started()
            logger.info(f"Camera started on port {camera_port}")

        except Exception as e:
            logger.exception("Error starting camera")
            self._is_running = False
            self.view.on_camera_error(str(e))

    def _stop_camera_impl(self) -> None:
        """Internal camera stop implementation."""
        try:
            # Unschedule polling
            if self._poll_event:
                Clock.unschedule(self._poll_event)
                self._poll_event = None

            # Stop camera service
            self.camera_service.stop()

            # Clear algorithm
            self.algorithm = None
            self._is_running = False

            # Notify view
            self.view.on_camera_stopped()
            logger.info("Camera stopped")

        except Exception as e:
            logger.exception("Error stopping camera")
            self.view.on_camera_error(str(e))

    # ============================================================
    # Frame Processing
    # ============================================================

    def _poll_frame_impl(self, dt) -> None:
        """Poll frames from camera service (called by Clock).

        Args:
            dt: Delta time from Clock
        """
        try:
            # if not self._is_running or not self.algorithm:
            #     return

            # Read frame from camera queue
            ret, frame = self.camera_service.read_now()
            if not ret or frame is None:
                return

            # Run prediction
            try:
                # predicted_frame, counter, name = self.algorithm.predict_webcam(frame)

                # Prepare prediction data
                prediction_data = {
                    'frame': frame,
                    'name': "unknown",
                    'counter': 2,
                    'confidence': 0.0  # TODO: Extract from algorithm if available
                }

                # Callback to view
                self.view.on_frame_received(prediction_data)

            except Exception as e:
                logger.exception("Error running prediction")

        except Exception as e:
            logger.exception("Error in frame polling")

    # ============================================================
    # Algorithm Management
    # ============================================================

    def _load_algorithm(self, model: ModelMetadata) -> bool:
        """Load ML algorithm from model.

        Args:
            model: ModelMetadata to load

        Returns:
            True if successful
        """
        try:
            if not model:
                raise ValueError("Model is None")

            # Use factory to create classifier
            self.algorithm = AlgorithmFactory.create(model)

            # Load model from disk
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

    # ============================================================
    # Photo Loading
    # ============================================================

    def load_photo_from_file(self) -> None:
        """Load photo from file dialog in background thread."""
        thread = threading.Thread(target=self._load_photo_threaded, daemon=True)
        thread.start()

    def _load_photo_threaded(self) -> None:
        """Background thread for file dialog and photo processing."""
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

            # Process image
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
        """Process image with loaded algorithm.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (frame, name) or None
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            if not self.algorithm:
                raise RuntimeError("Algorithm not loaded. Start camera first or select a model.")

            # Get prediction
            frame, name = self.algorithm.predict_from_image(image_path)

            logger.info(f"Image processed: {image_path} -> {name}")
            return frame, name

        except Exception as e:
            logger.exception(f"Error processing image: {image_path}")
            return None

    # ============================================================
    # State Queries
    # ============================================================

    def is_camera_running(self) -> bool:
        """Check if camera is currently running."""
        return self._is_running

    def is_algorithm_loaded(self) -> bool:
        """Check if algorithm is loaded."""
        return self.algorithm is not None
