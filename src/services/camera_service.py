import queue
import threading
import time
from functools import lru_cache
from typing import Optional, Tuple

import cv2

from core.logger import AppLogger

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

    def start(self, port) -> None:
        with self._lock:
            if self._running.is_set():
                logger.debug("CameraService already running")
                return

            logger.debug("Opening VideoCapture on port %s", port or self.port)
            self._capture = cv2.VideoCapture(self.port, cv2.CAP_DSHOW)
            if not self._capture.isOpened():
                raise CameraError(f"Unable to open camera on port {port or self.port}")

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

    @lru_cache(maxsize=None)
    def get_all_cameras(self, max_tests=10):
        available = []
        for index in range(max_tests):
            cap = cv2.VideoCapture(index)
            if cap is None or not cap.isOpened():
                continue
            ret, _ = cap.read()
            if ret:
                available.append(index)
            cap.release()
        return available
