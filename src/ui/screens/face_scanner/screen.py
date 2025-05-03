import csv
import shutil
import threading
from datetime import datetime
from typing import Optional

import cv2
import matplotlib.pyplot as plt
import numpy as np
from kivy.clock import mainthread
from kivy.core.image import Texture
from matplotlib.ticker import MaxNLocator

from core.config import config
from core.logger import AppLogger
from models.model.model_metadata import ModelMetadata
from services import camera_service, model_service, person_service
from ui.base_screen import BaseScreen
from ui.presenters.face_scanner_presenter import FaceScannerPresenter
from ui.screens.face_scanner.camera_presenter import WebCameraPresenter

logger = AppLogger().get_logger(__name__)


class FaceScanner(BaseScreen):
    """Face Scanner screen - main scanning and recognition interface."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.presenter = FaceScannerPresenter(view=self)
        self.camera_presenter = WebCameraPresenter(self.ids.camera, camera_service)

        self.loaded_image: Optional[np.ndarray] = None
        self.selected_model: Optional[ModelMetadata] = None
        self.camera_selected = ""

        self.person_service = person_service
        self.model_service = model_service
        self.camera_service = camera_service

        self._initialize()

    def _initialize(self) -> None:
        """Initialize screen resources."""
        try:
            if config.paths.TEMP_DIR.exists():
                shutil.rmtree(config.paths.TEMP_DIR)
            config.paths.TEMP_DIR.mkdir(parents=True, exist_ok=True)

            if not config.stats.FILE_STATS_CSV.exists():
                config.stats.FILE_STATS_CSV.parent.mkdir(parents=True, exist_ok=True)
                config.stats.FILE_STATS_CSV.touch()

            self.presenter.start()
            if available_models := self.model_service.registry.items:
                self.selected_model = available_models[0]
            logger.info("FaceScanner initialized")
        except Exception as e:
            logger.exception(f"Error initializing FaceScanner: {e}")
            self.show_error("Initialization Error", str(e))

    def refresh(self) -> None:
        """Called when screen is entered - update UI."""
        try:
            self.model_service.refresh()
            self.ids.model_name.values = self.presenter.get_available_models()
            self.ids.number_people_database_text.text = str(self.presenter.get_person_count())

            self._update_plot()
        except Exception as e:
            logger.exception("Error refreshing FaceScanner")
            self.show_error("Refresh Error", str(e))

    # ============================================================
    # Camera Controls
    # ============================================================

    def camera_on_off(self) -> None:
        """Toggle camera on/off."""
        thread = threading.Thread(target=self._toggle_camera, daemon=True)
        thread.start()

    @mainthread
    def _toggle_camera(self) -> None:
        """Background thread for camera toggle."""
        try:
            if self.loaded_image:
                self._clear_photo()

            self.person_service.refresh()
            self._disable_button(self.ids.identification_btn)

            # Start/stop camera via presenter
            if self.camera_service.is_running():
                self.presenter.stop_camera()
            else:
                camera_port = int(self.camera_selected.split()[-1])
                self.presenter.start_camera(camera_port, self.selected_model)

        except Exception as e:
            logger.exception("Error toggling camera")
            self.show_error("Camera Error", str(e))

    def _clear_photo(self) -> None:
        """Clear loaded photo."""
        try:
            self.ids.load_image_btn.text = config.ui.TEXTS["load_photo"]
            self.ids.camera.texture = None
            self.loaded_image = None
            self._disable_button(self.ids.identification_btn)
        except Exception as e:
            logger.exception("Error clearing photo")

    # ============================================================
    # Photo Loading
    # ============================================================

    def load_photo(self) -> None:
        """Load photo from file."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            if self.loaded_image:
                self._clear_photo()
                self._disable_button(self.ids.identification_btn)
                return

            root = tk.Tk()
            root.withdraw()

            photo_paths = filedialog.askopenfilenames(
                filetypes=[("Image files", ".jpeg .jpg .png")]
            )

            if photo_paths:
                image_path = photo_paths[0]
                result = self.presenter.load_photo(image_path)

                if result:
                    frame, name = result
                    self._display_image(frame)

                    if name.lower() == config.ui.TEXTS["unknown"].lower():
                        self._disable_button(self.ids.identification_btn)
                    else:
                        self._enable_button(self.ids.identification_btn, name)

                    self.ids.load_image_btn.text = config.ui.TEXTS["clear_photo"]
                    self.loaded_image = frame

            self.get_root_window().raise_window()

        except Exception as e:
            logger.exception("Error loading photo")
            self.show_error("Load Photo Error", str(e))

    def _display_image(self, frame: np.ndarray) -> None:
        """Display image in camera widget.

        Args:
            frame: Image frame to display
        """
        try:
            buf = cv2.flip(frame, 0).tobytes()
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt="rgb"
            )
            texture.blit_buffer(buf, colorfmt="rgb", bufferfmt="ubyte")
            self.ids.camera.texture = texture
        except Exception as e:
            logger.exception("Error displaying image")

    # ============================================================
    # Model Selection
    # ============================================================

    def on_spinner_model_select(self, model_name: str) -> None:
        try:
            self.selected_model = self.model_service.get_model(model_name)
            self.ids.number_people_model_text.text = str(len(self.selected_model.train_dataset_Y))
        except Exception as e:
            logger.exception(f"Error selecting model {model_name}")

    # ============================================================
    # Camera Selection
    # ============================================================

    def set_text_camera_spinner(self) -> str:
        self.camera_selected = config.CAMERA_PORTS[0]
        return self.camera_selected

    def get_values_camera(self) -> list:
        return config.CAMERA_PORTS if config.CAMERA_PORTS else ["N/A"]

    def on_spinner_camera_select(self, camera: str) -> None:
        self.camera_selected = camera

    # ============================================================
    # Statistics
    # ============================================================

    def read_plot(self) -> str:
        """Read and generate statistics plot.

        Returns:
            Path to plot image
        """
        try:
            data_csv = []
            if config.stats.FILE_STATS_CSV.exists():
                with open(config.stats.FILE_STATS_CSV, 'r') as csvfile:
                    file_rd = csv.reader(csvfile, delimiter=',')
                    for row in file_rd:
                        data_csv.append(row)

            if not data_csv:
                self._create_blank_plot()
                return str(config.stats.FILE_RESULT_PLOT)

            # Process data and create plot
            ok_y, nok_y, nnok_y, x = self._process_stats_data(data_csv)

            if x:
                self._create_plot(x, ok_y, nok_y, nnok_y)
            else:
                self._create_blank_plot()

            return str(config.stats.FILE_RESULT_PLOT)

        except Exception as e:
            logger.exception("Error reading plot")
            self._create_blank_plot()
            return str(config.stats.FILE_RESULT_PLOT)

    def _process_stats_data(self, data_csv: list) -> tuple:
        """Process statistics CSV data.

        Args:
            data_csv: CSV data as list of lists

        Returns:
            Tuple of (ok_y, nok_y, nnok_y, x) lists
        """
        now = datetime.now()
        current_hour = now.hour
        current_day = now.day

        range_hours = []
        if current_hour - 11 < 0:
            first_hour = 24 - (11 - current_hour)
        else:
            first_hour = current_hour - 11

        for hour in range(12):
            range_hours.append((first_hour + hour) % 24)

        x, ok_y, nok_y, nnok_y = [], [], [], []

        for hour in range_hours:
            ok, nok, nnok = 0, 0, 0
            for element in data_csv:
                try:
                    if int(element[0]) == hour:
                        nnok += int(element[3])
                        ok += int(element[4])
                        nok += int(element[5])
                except (ValueError, IndexError):
                    continue

            x.append(hour)
            nnok_y.append(max(0, nnok - nok - ok))
            nok_y.append(nok)
            ok_y.append(ok)

        return ok_y, nok_y, nnok_y, x

    def _create_plot(self, x: list, ok_y: list, nok_y: list, nnok_y: list) -> None:
        """Create statistics plot.

        Args:
            x: X-axis data (hours)
            ok_y: Correct identifications
            nok_y: Incorrect identifications
            nnok_y: No identifications
        """
        try:
            series1 = np.array(ok_y)
            series2 = np.array(nok_y)
            series3 = np.array(nnok_y)

            index = np.arange(len(x))
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)')
            plt.ylabel('Count of identificated')
            plt.xlabel('Hour')

            plt.bar(index, series1, color="g", label="Correct")
            plt.bar(index, series2, color="r", bottom=series1, label="Incorrect")
            plt.bar(index, series3, color="b", bottom=(series2 + series1), label="No ID")

            plt.xticks(index, x)
            ax = plt.gca()
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis='y')
            plt.legend()

            plt.savefig(config.stats.FILE_RESULT_PLOT)
            plt.close()

        except Exception as e:
            logger.exception("Error creating plot")

    def _create_blank_plot(self) -> None:
        """Create blank plot."""
        try:
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)')
            plt.ylabel('Count of identificated')
            plt.xlabel('Hour')
            plt.savefig(config.stats.FILE_RESULT_PLOT)
            plt.close()
        except Exception as e:
            logger.exception("Error creating blank plot")

    def clear_stats(self) -> None:
        """Clear statistics."""
        try:
            current_hour = TimeUtils.get_hour()
            current_day = TimeUtils.get_day()
            current_month = TimeUtils.get_month()

            range_hours = []
            if current_hour - 11 < 0:
                first_hour = 24 - current_hour - 11
            else:
                first_hour = current_hour - 11

            for hour in range(12):
                range_hours.append(first_hour + hour)

            with open(config.stats.FILE_STATS_CSV, "w", newline='') as gen_file:
                writing = csv.writer(gen_file, delimiter=',')
                for hour in range_hours:
                    data = [hour, current_day - 1 if hour > current_hour else current_day,
                            current_month, 0, 0, 0]
                    writing.writerow(data)

            self._create_blank_plot()
            self._update_plot()
            self.show_info("Statistics cleared")

        except Exception as e:
            logger.exception("Error clearing stats")

    def _update_plot(self) -> None:
        """Update plot display."""
        try:
            plot_path = self.read_plot()
            if self.ids.plot:
                self.ids.plot.source = str(plot_path)
                self.ids.plot.reload()
        except Exception as e:
            logger.exception("Error updating plot")

    # ============================================================
    # Person Identification
    # ============================================================

    def switch_on_person(self, name: str) -> None:
        try:
            if self.camera_service.is_running():
                self.presenter.stop_camera()

            self.presenter.show_person_info(name)

        except Exception as e:
            logger.exception(f"Error switching person {name}")

    # ============================================================
    # Result Recording
    # ============================================================

    def its_ok(self) -> None:
        """Record correct identification."""
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            hour = TimeUtils.get_hour()
            day = TimeUtils.get_day()
            month = TimeUtils.get_month()
            data = [hour, day, month, 0, 1, 0]

            with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
                writing = csv.writer(gen_file, delimiter=',')
                writing.writerow(data)

            self._update_plot()

        except Exception as e:
            logger.exception("Error recording OK result")

    def its_nok(self) -> None:
        """Record incorrect identification."""
        try:
            self._disable_button(self.ids.its_ok_btn)
            self._disable_button(self.ids.its_nok_btn)

            hour = TimeUtils.get_hour()
            day = TimeUtils.get_day()
            month = TimeUtils.get_month()
            data = [hour, day, month, 0, 0, 1]

            with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
                writing = csv.writer(gen_file, delimiter=',')
                writing.writerow(data)

            self._update_plot()

        except Exception as e:
            logger.exception("Error recording NOK result")

    def its_add_one(self) -> None:
        """Record identification attempt."""
        try:
            hour = TimeUtils.get_hour()
            day = TimeUtils.get_day()
            month = TimeUtils.get_month()
            data = [hour, day, month, 1, 0, 0]

            with open(config.stats.FILE_STATS_CSV, "a", newline='') as gen_file:
                writing = csv.writer(gen_file, delimiter=',')
                writing.writerow(data)

            self._update_plot()

        except Exception as e:
            logger.exception("Error recording attempt")

    # ============================================================
    # UI Helpers
    # ============================================================
    @mainthread
    def _disable_button(self, button) -> None:
        """Disable button.

        Args:
            button: Button widget
        """
        try:
            button.disabled = True
            button.opacity = 0.5
        except Exception as e:
            logger.exception("Error disabling button")

    def _enable_button(self, button, name: str = '') -> None:
        """Enable button.

        Args:
            button: Button widget
            name: Optional text for button
        """
        try:
            if button == self.ids.identification_btn:
                button.text = name
                self._enable_button(self.ids.its_ok_btn)
                self._enable_button(self.ids.its_nok_btn)
                self.its_add_one()

            button.disabled = False
            button.opacity = 1.0
        except Exception as e:
            logger.exception("Error enabling button")

    def disable_button(self, button) -> bool:
        """Check if button should be disabled.

        Args:
            button: Button widget

        Returns:
            True if should be disabled
        """
        return button.disabled

    def enable_button(self, button) -> bool:
        """Check if button should be enabled.

        Args:
            button: Button widget

        Returns:
            True if should be enabled
        """
        return not button.disabled

    def popup_photo(self) -> None:
        """Show photo in popup."""
        try:
            if config.stats.FILE_RESULT_PLOT.exists():
                from src.ui.popups.plot import PlotPopup
                popup = PlotPopup(str(config.stats.FILE_RESULT_PLOT))
                popup.open()
        except Exception as e:
            logger.exception("Error showing popup")

    # ============================================================
    # Cleanup
    # ============================================================

    def on_leave(self) -> None:
        """Called when screen is left."""
        try:
            self.presenter.stop()
            logger.info("FaceScanner screen left")
        except Exception as e:
            logger.exception("Error on screen leave")
