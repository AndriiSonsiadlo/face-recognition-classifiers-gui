from typing import Optional

import cv2
import numpy as np
from kivy.clock import mainthread
from kivy.core.image import Image as CoreImage
from kivy.core.image import Texture

from core import config
from services import camera_service, person_service
from ui.base_screen import BaseScreen
from ui.popups.warn import WarnPopup
from ui.presenters import FaceScannerPresenter
from ui.presenters.camera_presenter import WebCameraPresenter


class FaceScanner(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)

        self.camera_presenter: Optional[WebCameraPresenter] = None
        self.presenter: Optional['FaceScannerPresenter'] = None

        self.loaded_image: Optional[np.ndarray] = None
        self.last_camera_frame: Optional[np.ndarray] = None
        self.last_identified_name: str = ""
        self.is_camera_mode: bool = False

        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = FaceScannerPresenter(self)
            self.camera_presenter = WebCameraPresenter(self, camera_service)

            self.presenter.start()
            self.camera_presenter.start()

            self._reset_identification()

            self.logger.info("FaceScanner initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing FaceScanner: {e}")
            self.show_error("Initialization Error", str(e))

    def on_spinner_model_select(self, model_name: str) -> str:
        if self.presenter:
            self.presenter.select_model(model_name)
            self._on_model_loaded()
        return self.presenter.selected_model

    def on_spinner_camera_select(self, camera_port: str) -> None:
        if self.presenter:
            self.presenter.select_camera(camera_port)
        self.logger.debug(f"Selected camera: {camera_port}")

    def get_ui_text_camera_button(self) -> str:
        return config.ui.TEXTS.get("start_webcam", "Turn on")

    def camera_on_off(self) -> None:
        if self.camera_presenter:
            if not self.camera_presenter.is_camera_running():
                self._clear_photo()

            self.camera_presenter.toggle_camera(
                self.presenter.selected_camera,
                self.presenter.selected_model
            )

    def on_camera_started(self) -> None:
        self.is_camera_mode = True
        self.last_identified_name = ""
        self._update_camera_ui_started()

    def on_camera_stopped(self) -> None:
        self.is_camera_mode = False
        self._update_camera_ui_stopped()

    def on_frame_received(self, prediction_data: dict) -> None:
        try:
            self.last_camera_frame = prediction_data['frame'].copy()

            self._display_frame(prediction_data['frame'])
            self._handle_prediction(
                prediction_data['counter'],
                prediction_data['name']
            )
        except Exception as e:
            self.logger.exception("Error handling frame prediction")

    def on_camera_error(self, error_msg: str) -> None:
        self.show_error("Camera Error", error_msg)

    @mainthread
    def load_photo(self) -> None:
        try:
            if self.loaded_image is not None:
                self._clear_photo()
                return

            if self.camera_presenter and self.camera_presenter.is_camera_running():
                self.camera_presenter.toggle_camera(
                    self.presenter.selected_camera,
                    self.presenter.selected_model
                )
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._load_photo_delayed(), 0.1)
                return

            self._load_photo_delayed()

        except Exception as e:
            self.logger.exception("Error loading photo")
            self.show_error("Load Photo Error", str(e))

    def _load_photo_delayed(self) -> None:
        try:
            if not self.camera_presenter:
                self.show_error("Error", "Camera presenter not initialized")
                return

            self.camera_presenter.load_photo_from_file(self.presenter.selected_model)

        except Exception as e:
            self.logger.exception("Error in delayed photo load")
            self.show_error("Load Photo Error", str(e))

    @mainthread
    def on_photo_loaded(self, frame: np.ndarray, name: str) -> None:
        try:
            self.is_camera_mode = False
            self._display_frame(frame)

            unknown = config.ui.TEXTS["unknown"]
            if name.lower() == unknown.lower():
                self._disable_button(self.ids.identification_btn)
                self.ids.identification_btn.text = "Unknown"
                self._disable_button(self.ids.its_ok_btn)
                self._disable_button(self.ids.its_nok_btn)
            else:
                self._enable_button(self.ids.identification_btn)
                self.ids.identification_btn.text = name
                self._enable_button(self.ids.its_ok_btn)
                self._enable_button(self.ids.its_nok_btn)

            self.ids.load_image_btn.text = config.ui.TEXTS["clear_photo"]
            self.loaded_image = frame

        except Exception as e:
            self.logger.exception("Error handling loaded photo")

    def on_photo_error(self, error_msg: str) -> None:
        self.show_error("Photo Error", error_msg)

    def _clear_photo(self) -> None:
        try:
            self.ids.load_image_btn.text = config.ui.TEXTS["load_photo"]
            self.ids.camera.texture = CoreImage(str(config.images.CAMERA_DISABLED_IMAGE)).texture

            self.loaded_image = None
            self._reset_identification()
        except Exception as e:
            self.logger.exception("Error clearing photo")

    def read_plot(self) -> str:
        if self.presenter:
            return self.presenter.get_plot_path()
        return ""

    def clear_stats(self) -> None:
        if self.presenter:
            self.presenter.clear_statistics()
            self.show_info("Statistics cleared")

    def on_plot_updated(self) -> None:
        self._update_plot()

    def its_ok(self) -> None:
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            if self.presenter:
                self.presenter.record_identification(success=True)
                self.on_plot_updated()

        except Exception as e:
            self.logger.exception("Error recording OK result")

    def its_nok(self) -> None:
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            if self.presenter:
                self.presenter.record_identification(success=False)
                self.on_plot_updated()

        except Exception as e:
            self.logger.exception("Error recording NOK result")

    def its_add_one(self) -> None:
        try:
            if self.presenter:
                self.presenter.record_attempt()
                self.on_plot_updated()
        except Exception as e:
            self.logger.exception("Error recording attempt")

    def switch_on_person(self, name: str) -> None:
        try:
            person = person_service.get_person(name)
            if person:
                from ui.popups.person_info import PersonInfoPopup
                PersonInfoPopup(person=person).open()
            else:
                WarnPopup(title=f"{name} not found in database").open()

            self.logger.info(f"Switch to person: {name}")

        except Exception as e:
            self.logger.exception(f"Error switching person {name}")

    @mainthread
    def _update_camera_ui_started(self) -> None:
        try:
            if hasattr(self.ids, 'on_off_btn'):
                self.ids.on_off_btn.text = config.ui.TEXTS["stop_webcam"]
            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = "N/A"
                self._disable_button(self.ids.identification_btn)
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)
        except Exception as e:
            self.logger.exception("Error updating camera start UI")

    @mainthread
    def _update_camera_ui_stopped(self) -> None:
        try:
            if hasattr(self.ids, 'on_off_btn'):
                self.ids.on_off_btn.text = config.ui.TEXTS["start_webcam"]

            if self.last_identified_name and self.last_identified_name != "N/A":
                self._enable_button(self.ids.identification_btn)
                self.ids.identification_btn.text = self.last_identified_name

                self._enable_button(self.ids.its_ok_btn)
                self._enable_button(self.ids.its_nok_btn)
            else:
                if hasattr(self.ids, 'camera'):
                    if self.loaded_image is None and self.last_camera_frame is None:
                        self._clear_photo()

                self._disable_button(self.ids.identification_btn)
                self._disable_button(self.ids.its_ok_btn)
                self._disable_button(self.ids.its_nok_btn)

        except Exception as e:
            self.logger.exception("Error updating camera stop UI")

    @mainthread
    def _display_frame(self, frame: np.ndarray) -> None:
        try:
            if not hasattr(self.ids, 'camera'):
                return

            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt="rgb"
            )
            texture.blit_buffer(buf, colorfmt="rgb", bufferfmt="ubyte")
            self.ids.camera.texture = texture

        except Exception as e:
            self.logger.exception("Error displaying frame")

    @mainthread
    def _handle_prediction(self, counter: int, name: str) -> None:
        try:
            threshold = config.person.DEFAULT_COUNT_FRAME
            unknown = config.ui.TEXTS["unknown"]

            if counter >= threshold and name != unknown:
                self._set_identification(name)
            else:
                if self.is_camera_mode:
                    if name and name != unknown:
                        if hasattr(self.ids, 'identification_btn'):
                            self.ids.identification_btn.text = name
                            self._disable_button(self.ids.identification_btn)
                    else:
                        if hasattr(self.ids, 'identification_btn'):
                            self.ids.identification_btn.text = "N/A"
                            self._disable_button(self.ids.identification_btn)

        except Exception as e:
            self.logger.exception("Error handling prediction")

    @mainthread
    def _set_identification(self, name: str) -> None:
        try:
            self.last_identified_name = name

            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = name
                self._enable_button(self.ids.identification_btn)

            if not self.is_camera_mode or not self.camera_presenter.is_camera_running():
                self._enable_button(self.ids.its_ok_btn)
                self._enable_button(self.ids.its_nok_btn)
            else:
                self._disable_button(self.ids.its_ok_btn)
                self._disable_button(self.ids.its_nok_btn)

        except Exception as e:
            self.logger.exception("Error setting identification")

    @mainthread
    def _reset_identification(self) -> None:
        try:
            if hasattr(self.ids, 'identification_btn'):
                self.ids.identification_btn.text = "N/A"
                self._disable_button(self.ids.identification_btn)
                self._disable_button(self.ids.its_ok_btn)
                self._disable_button(self.ids.its_nok_btn)

        except Exception as e:
            self.logger.exception("Error resetting identification")

    @mainthread
    def _disable_button(self, button) -> None:
        try:
            button.disabled = True
            button.opacity = 0.5
        except Exception as e:
            self.logger.exception("Error disabling button")

    @mainthread
    def _enable_button(self, button) -> None:
        try:
            button.disabled = False
            button.opacity = 1.0
        except Exception as e:
            self.logger.exception("Error enabling button")

    def disable_button(self, button) -> bool:
        try:
            return button.disabled
        except:
            return True

    def enable_button(self, button) -> bool:
        try:
            return not button.disabled
        except:
            return False

    @mainthread
    def _update_plot(self) -> None:
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
        try:
            if self.presenter and hasattr(self.ids, 'number_people_model_text'):
                count = self.presenter.get_model_person_count()
                self.ids.number_people_model_text.text = str(count)
        except Exception as e:
            self.logger.exception("Error updating model UI")

    def popup_photo(self) -> None:
        try:
            if config.stats.FILE_RESULT_PLOT.exists():
                from ui.popups.plot import PlotPopup
                popup = PlotPopup(str(config.stats.FILE_RESULT_PLOT))
                popup.open()
        except Exception as e:
            self.logger.exception("Error showing popup")

    def on_leave(self) -> None:
        try:
            if self.camera_presenter:
                self.camera_presenter.stop()
            if self.presenter:
                self.presenter.stop()

            self.last_camera_frame = None
            self.loaded_image = None
            self.last_identified_name = ""
            self.is_camera_mode = False

            self.logger.info("FaceScanner screen left")
        except Exception as e:
            self.logger.exception("Error on screen leave")
