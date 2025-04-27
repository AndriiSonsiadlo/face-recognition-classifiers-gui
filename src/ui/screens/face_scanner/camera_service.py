import queue
import threading
import time
from typing import Optional, Tuple

import cv2

from utils.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class CameraError(Exception):
    pass


class CameraService:
    """Service responsible for interacting with the OpenCV camera.

    - Runs a background thread that reads frames from the camera.
    - Publishes frames to a thread-safe queue for consumers (presenter).
    - Exposes start/stop and simple health checks.
    """

    def __init__(self, port: int = 0, fps: int = 30, queue_size: int = 2):
        self.port = port
        self.fps = fps
        self._capture: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self.frames: "queue.Queue[Tuple[bool, Optional[object]]]" = queue.Queue(maxsize=queue_size)
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._running.is_set():
                logger.debug("CameraService already running")
                return

            logger.debug("Opening VideoCapture on port %s", self.port)
            self._capture = cv2.VideoCapture(self.port, cv2.CAP_DSHOW)
            if not self._capture.isOpened():
                raise CameraError(f"Unable to open camera on port {self.port}")

            self._running.set()
            self._thread = threading.Thread(target=self._run, name="CameraReadThread", daemon=True)
            self._thread.start()
            logger.info("CameraService started")

    def stop(self) -> None:
        with self._lock:
            self._running.clear()
            if self._thread and self._thread.is_alive():
                logger.debug("Waiting for camera thread to finish")
                self._thread.join(timeout=1.0)

            if self._capture:
                try:
                    self._capture.release()
                except Exception:
                    logger.exception("Error releasing capture")
                finally:
                    self._capture = None

            # empty queue
            while not self.frames.empty():
                try:
                    self.frames.get_nowait()
                except queue.Empty:
                    break

            logger.info("CameraService stopped")

    def _run(self) -> None:
        target_dt = 1.0 / max(1, self.fps)
        logger.debug("Camera thread running with target dt=%s", target_dt)
        while self._running.is_set():
            start = time.time()
            try:
                ret, frame = self._capture.read()  # type: ignore[attr-defined]
            except Exception as exc:
                logger.exception("Exception reading frame: %s", exc)
                ret, frame = False, None

            try:
                # non-blocking put; if queue full, drop oldest and put again
                if not self.frames.full():
                    self.frames.put_nowait((ret, frame))
                else:
                    try:
                        _ = self.frames.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self.frames.put_nowait((ret, frame))
                    except queue.Full:
                        logger.warning("Frame queue full, dropping frame")
            except Exception:
                logger.exception("Failed to enqueue frame")

            elapsed = time.time() - start
            to_sleep = target_dt - elapsed
            if to_sleep > 0:
                time.sleep(to_sleep)

    def read_now(self) -> Tuple[bool, Optional[object]]:
        """Read the most recent frame from the queue (non-blocking).

        Returns a tuple (ret, frame). If queue empty, returns (False, None).
        """
        try:
            return self.frames.get_nowait()
        except queue.Empty:
            return False, None

    def is_running(self) -> bool:
        return self._running.is_set()

# ----------------------------
# file: view_webcamera.py
# ----------------------------

# # ----------------------------
# # file: main_integration.py
# # ----------------------------
# """
# Example integration showing how to wire up the MVP components with dependency injection.
#
# This is an integration scaffold — adapt it to your actual Kivy App structure.
# """
# from pathlib import Path
#
# from presenter import WebCameraPresenter
# from utils.logger import AppLogger
#
# logger = AppLogger().get_logger(__name__)
#
#
# def build_webcamera_component(parent_widget, model_algorithm: str = None, model_path: str = None, port: int = 0, fps: int = 30):
#     """Create and wire view + presenter + service. Return the view instance to embed in your Kivy layout."""
#
#     # 1) Camera service (DI)
#     camera_service = CameraService(port=port, fps=fps)
#
#     # 2) Model config
#     model_config = ModelConfig(algorithm=model_algorithm, path_file_model=model_path)
#
#     # 3) View (Kivy widget)
#     view = WebCameraView()
#     parent_widget.add_widget(view)
#
#     # 4) Presenter (injects service & model)
#     presenter = WebCameraPresenter(view=view, camera_service=camera_service, model_config=model_config)
#     view.presenter = presenter
#
#     return view, presenter


# Example usage in your Kivy app:
# view, presenter = build_webcamera_component(main_screen, model_algorithm=config.model.ALGORITHM_KNN, model_path='/path/to/model')
# Bind your start/stop buttons to view.on_start_button_pressed / view.on_stop_button_pressed


# ----------------------------
# Notes
# ----------------------------
# - Each file section above should be saved as its own module for clarity.
# - The CameraService runs an independent thread that continually reads from the cv2.VideoCapture
#   and places frames into a sized queue. The Presenter polls that queue on the Kivy mainloop
#   and delegates ML predictions and view updates.
# - Errors are logged, and the view gets notified about fatal failures via show_error.
# - You can extend AlgorithmWrapper to support more ML loaders or lazy-loading behavior.
# - This structure enables unit-testing of Presenter and CameraService independently.
# - Make sure 'core.config' and the ML algorithm classes remain compatible with the new wrappers.
