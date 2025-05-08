from typing import Optional

import cv2
import numpy as np
from kivy.clock import mainthread
from kivy.core.image import Texture

from core import config
from services import camera_service
from ui.base_screen import BaseScreen
from ui.presenters import FaceScannerPresenter
from ui.presenters.camera_presenter import WebCameraPresenter


class FaceScanner(BaseScreen):
    """Face Scanner Screen - View in MVP architecture.

    Responsibilities:
    - UI rendering and layout
    - User input handling
    - Delegates business logic to presenters
    - Updates based on presenter callbacks
    """

    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)

        self.camera_presenter: Optional[WebCameraPresenter] = None
        self.presenter: Optional['FaceScannerPresenter'] = None

        self.loaded_image: Optional[np.ndarray] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize screen resources."""
        try:
            # Initialize presenters
            self.presenter = FaceScannerPresenter(self)
            self.camera_presenter = WebCameraPresenter(self, camera_service)

            # Start presenter operations
            self.presenter.start()
            self.camera_presenter.start()

            self.logger.info("FaceScanner initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing FaceScanner: {e}")
            self.show_error("Initialization Error", str(e))

    # ============================================================
    # Spinner Callbacks (from UI)
    # ============================================================

    def on_spinner_model_select(self, model_name: str) -> str:
        """Handle model selection."""
        if self.presenter:
            self.presenter.select_model(model_name)
            self._on_model_loaded()
        return self.presenter.selected_model

    def on_spinner_camera_select(self, camera_port: str) -> None:
        """Handle camera selection."""
        if self.presenter:
            self.presenter.select_camera(camera_port)
        self.logger.debug(f"Selected camera: {camera_port}")

    def get_ui_text_camera_button(self) -> str:
        """Get camera button text (start/stop)."""
        return config.ui.TEXTS.get("start_webcam", "Turn on")

    # ============================================================
    # Camera Control (delegates to presenter)
    # ============================================================

    def camera_on_off(self) -> None:
        """Toggle camera on/off."""
        if self.camera_presenter:
            self.camera_presenter.toggle_camera(self.presenter.selected_camera, self.presenter.selected_model)

    def on_camera_started(self) -> None:
        """Callback from presenter when camera starts."""
        self._update_camera_ui_started()

    def on_camera_stopped(self) -> None:
        """Callback from presenter when camera stops."""
        self._update_camera_ui_stopped()

    def on_frame_received(self, prediction_data: dict) -> None:
        """Callback from presenter with prediction results.

        Args:
            prediction_data: {
                'frame': np.ndarray,
                'name': str,
                'counter': int,
                'confidence': float
            }
        """
        try:
            self._display_frame(prediction_data['frame'])
            self._handle_prediction(
                prediction_data['counter'],
                prediction_data['name']
            )
        except Exception as e:
            self.logger.exception("Error handling frame prediction")

    def on_camera_error(self, error_msg: str) -> None:
        """Callback from presenter on camera error."""
        self.show_error("Camera Error", error_msg)

    # ============================================================
    # Photo Loading (delegates to presenter)
    # ============================================================

    @mainthread
    def load_photo(self) -> None:
        """Load photo from file for recognition."""
        try:
            # Clear if already loaded
            if self.loaded_image is not None:
                self._clear_photo()

                return

            if not self.camera_presenter:
                self.show_error("Error", "Camera presenter not initialized")
                return

            # Delegate to presenter
            self.camera_presenter.load_photo_from_file()

        except Exception as e:
            self.logger.exception("Error loading photo")
            self.show_error("Load Photo Error", str(e))

    def on_photo_loaded(self, frame: np.ndarray, name: str) -> None:
        """Callback from presenter when photo is loaded and processed."""
        try:
            self._display_frame(frame)

            unknown = config.ui.TEXTS["unknown"]
            if name.lower() == unknown.lower():
                self._disable_button(self.ids.identification_btn)
                self.ids.identification_btn.text = "Unknown"
            else:
                self._enable_button(self.ids.identification_btn)
                self.ids.identification_btn.text = name

            self.ids.load_image_btn.text = config.ui.TEXTS["clear_photo"]
            self.loaded_image = frame

            # Enable result buttons
            self._enable_button(self.ids.its_ok_btn)
            self._enable_button(self.ids.its_nok_btn)

        except Exception as e:
            self.logger.exception("Error handling loaded photo")

    def on_photo_error(self, error_msg: str) -> None:
        """Callback from presenter on photo loading error."""
        self.show_error("Photo Error", error_msg)

    def _clear_photo(self) -> None:
        """Clear loaded photo."""
        try:
            self.ids.load_image_btn.text = config.ui.TEXTS["load_photo"]
            self.ids.camera.texture = None
            self.loaded_image = None
            self._disable_button(self.ids.identification_btn)
        except Exception as e:
            self.logger.exception("Error clearing photo")

    # ============================================================
    # Statistics & Plotting (delegates to presenter)
    # ============================================================

    def read_plot(self) -> str:
        """Get statistics plot path."""
        if self.presenter:
            return self.presenter.get_plot_path()
        return ""

    def clear_stats(self) -> None:
        """Clear statistics."""
        if self.presenter:
            self.presenter.clear_statistics()
            self.show_info("Statistics cleared")

    def on_plot_updated(self) -> None:
        """Callback from presenter when plot is updated."""
        self._update_plot()

    def its_ok(self) -> None:
        """Record correct identification."""
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            if self.presenter:
                self.presenter.record_identification(success=True)
                self.on_plot_updated()

        except Exception as e:
            self.logger.exception("Error recording OK result")

    def its_nok(self) -> None:
        """Record incorrect identification."""
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            if self.presenter:
                self.presenter.record_identification(success=False)
                self.on_plot_updated()

        except Exception as e:
            self.logger.exception("Error recording NOK result")

    def its_add_one(self) -> None:
        """Record identification attempt."""
        try:
            if self.presenter:
                self.presenter.record_attempt()
                self.on_plot_updated()
        except Exception as e:
            self.logger.exception("Error recording attempt")

    # ============================================================
    # Person Info
    # ============================================================

    def switch_on_person(self, name: str) -> None:
        """Show person info and stop camera."""
        try:
            if self.camera_presenter:
                self.camera_presenter.stop()

            # TODO: Show person info popup
            self.logger.info(f"Switch to person: {name}")

        except Exception as e:
            self.logger.exception(f"Error switching person {name}")

    # ============================================================
    # UI Helpers (Internal)
    # ============================================================

    @mainthread
    def _update_camera_ui_started(self) -> None:
        """Update UI when camera starts."""
        try:
            if hasattr(self.ids, 'on_off_btn'):
                self.ids.on_off_btn.text = config.ui.TEXTS["stop_webcam"]
            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = "N/A"
                self._disable_button(self.ids.identification_btn)
        except Exception as e:
            self.logger.exception("Error updating camera start UI")

    @mainthread
    def _update_camera_ui_stopped(self) -> None:
        """Update UI when camera stops."""
        try:
            if hasattr(self.ids, 'on_off_btn'):
                self.ids.on_off_btn.text = config.ui.TEXTS["start_webcam"]
            if hasattr(self.ids, 'camera'):
                self.ids.camera.texture = None
            self._disable_button(self.ids.identification_btn)
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)
        except Exception as e:
            self.logger.exception("Error updating camera stop UI")

    @mainthread
    def _display_frame(self, frame: np.ndarray) -> None:
        """Display frame in camera widget."""
        try:
            if not hasattr(self.ids, 'camera'):
                return

            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt="bgr"
            )
            texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
            self.ids.camera.texture = texture

        except Exception as e:
            self.logger.exception("Error displaying frame")

    @mainthread
    def _handle_prediction(self, counter: int, name: str) -> None:
        """Handle prediction result."""
        try:
            threshold = config.person.DEFAULT_COUNT_FRAME
            unknown = config.ui.TEXTS["unknown"]

            if counter >= threshold and name != unknown:
                self._set_identification(name)
            else:
                self._reset_identification()

        except Exception as e:
            self.logger.exception("Error handling prediction")

    @mainthread
    def _set_identification(self, name: str) -> None:
        """Set identification display."""
        try:
            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = name
                self.ids.identification_btn.disabled = False
                self.ids.identification_btn.opacity = 1.0

            self._enable_button(self.ids.its_ok_btn)
            self._enable_button(self.ids.its_nok_btn)

        except Exception as e:
            self.logger.exception("Error setting identification")

    @mainthread
    def _reset_identification(self) -> None:
        """Reset identification display."""
        try:
            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = "N/A"
                self._disable_button(self.ids.identification_btn)

        except Exception as e:
            self.logger.exception("Error resetting identification")

    @mainthread
    def _disable_button(self, button) -> None:
        """Disable button."""
        try:
            button.disabled = True
            button.opacity = 0.5
        except Exception as e:
            self.logger.exception("Error disabling button")

    @mainthread
    def _enable_button(self, button) -> None:
        """Enable button."""
        try:
            button.disabled = False
            button.opacity = 1.0
        except Exception as e:
            self.logger.exception("Error enabling button")

    def disable_button(self, button) -> bool:
        """Check if button is disabled."""
        try:
            return button.disabled
        except:
            return True

    def enable_button(self, button) -> bool:
        """Check if button is enabled."""
        try:
            return not button.disabled
        except:
            return False

    @mainthread
    def _update_plot(self) -> None:
        """Update plot display."""
        try:
            plot_path = self.read_plot()
            if hasattr(self.ids, 'plot') and plot_path:
                self.ids.plot.source = str(plot_path)
                if hasattr(self.ids.plot, 'reload'):
                    self.ids.plot.reload()
        except Exception as e:
            self.logger.exception("Error updating plot")

    @mainthread
    def _on_model_loaded(self) -> None:
        """Update UI after model is selected."""
        try:
            if self.presenter and hasattr(self.ids, 'number_people_model_text'):
                count = self.presenter.get_model_person_count()
                self.ids.number_people_model_text.text = str(count)
        except Exception as e:
            self.logger.exception("Error updating model UI")

    def popup_photo(self) -> None:
        """Show photo in popup."""
        try:
            if config.stats.FILE_RESULT_PLOT.exists():
                from ui.popups.plot import PlotPopup
                popup = PlotPopup(str(config.stats.FILE_RESULT_PLOT))
                popup.open()
        except Exception as e:
            self.logger.exception("Error showing popup")

    # ============================================================
    # Lifecycle
    # ============================================================

    def on_leave(self) -> None:
        """Called when screen is left - cleanup."""
        try:
            if self.camera_presenter:
                self.camera_presenter.stop()
            if self.presenter:
                self.presenter.stop()
            self.logger.info("FaceScanner screen left")
        except Exception as e:
            self.logger.exception("Error on screen leave")
