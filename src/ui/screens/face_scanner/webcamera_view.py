import cv2
from kivy.clock import mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.uix.image import Image

from core import config
from core.logger import AppLogger

logger = AppLogger().get_logger(__name__)


class WebCameraView(Image):
    """Kivy View - thin wrapper - delegates logic to presenter."""

    def __init__(self, presenter=None, **kwargs):
        super().__init__(**kwargs)
        self.presenter = presenter
        self.clear_texture()

    def clear_texture(self):
        try:
            self.texture = CoreImage(str(config.images.CAMERA_DISABLED_IMAGE)).texture
        except Exception:
            logger.exception("Failed to set default texture")

    def on_start_button_pressed(self):
        if self.presenter:
            self.presenter.start()

    def on_stop_button_pressed(self):
        if self.presenter:
            self.presenter.stop()

    @mainthread
    def render_frame(self, frame):
        try:
            buf = cv2.flip(frame, 0).tobytes()
            tex = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
            tex.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
            self.texture = tex
        except Exception:
            logger.exception("Error rendering frame")

    @mainthread
    def on_camera_started(self):
        # update UI (buttons texts, disable/enable controls)
        try:
            if self.parent and hasattr(self.parent, "ids"):
                self.parent.ids.on_off_btn.text = config.ui.TEXTS["stop_webcam"]
        except Exception:
            logger.exception("Failed to update UI on camera start")

    @mainthread
    def on_camera_stopped(self):
        try:
            if self.parent and hasattr(self.parent, "ids"):
                self.parent.ids.on_off_btn.text = config.ui.TEXTS["start_webcam"]
        except Exception:
            logger.exception("Failed to update UI on camera stop")

    @mainthread
    def set_identification(self, name: str):
        try:
            if self.parent and hasattr(self.parent, "ids"):
                self.parent.ids.identification_btn.text = str(name)
                self.parent.ids.identification_btn.disabled = False
                self.parent.ids.identification_btn.opacity = 1
                # call additional UI flows
                self.parent.its_add_one()
        except Exception:
            logger.exception("Failed to set identification")

    @mainthread
    def reset_identification(self):
        try:
            if self.parent and hasattr(self.parent, "ids"):
                self.parent.ids.identification_btn.text = config.ui.TEXTS["unknown"]
                self.parent.ids.identification_btn.disabled = True
                self.parent.ids.identification_btn.opacity = 0.5
                self.parent.ids.its_ok_btn.disabled = True
                self.parent.ids.its_ok_btn.opacity = 0.5
                self.parent.ids.its_nok_btn.disabled = True
                self.parent.ids.its_nok_btn.opacity = 0.5
        except Exception:
            logger.exception("Failed to reset identification")

    @mainthread
    def show_error(self, message: str):
        logger.error("View error: %s", message)
        # Optionally show a popup; left to integrator
