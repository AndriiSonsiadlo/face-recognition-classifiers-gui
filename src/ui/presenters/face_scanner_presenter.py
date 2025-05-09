import csv
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from core import config
from core.logger import AppLogger
from services import person_service, model_service, camera_service
from ui.presenters.base_presenter import BasePresenter
from utils.TimeUtils import TimeUtils

logger = AppLogger().get_logger(__name__)


class FaceScannerPresenter(BasePresenter):
    """Presenter for FaceScanner - handles business logic.

    Responsibilities:
    - Model and person data management
    - Statistics recording and plotting
    - Delegates camera operations to WebCameraPresenter
    """

    def __init__(self, view):
        super().__init__(view)
        self.selected_camera = None
        self.selected_model = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        """Initialize data from registries."""
        try:
            model_service.refresh()
            person_service.refresh()

            models = model_service.get_all_models()
            if models:
                self.selected_model = models[0]

            cameras = camera_service.get_all_cameras()
            if cameras:
                self.selected_camera = cameras[0]

            logger.info("FaceScannerPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing FaceScannerPresenter")

    def start(self) -> None:
        """Start presenter operations."""
        try:
            self._update_view()
            logger.info("FaceScannerPresenter started")
        except Exception as e:
            logger.exception("Error starting FaceScannerPresenter")

    def stop(self) -> None:
        """Stop presenter operations."""
        logger.info("FaceScannerPresenter stopped")

    def refresh(self) -> None:
        """Refresh data and UI."""
        try:
            model_service.refresh()
            person_service.refresh()
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing FaceScannerPresenter")

    def _update_view(self) -> None:
        """Update view with current data."""
        try:
            # Update model count in view
            if self.selected_model and hasattr(self.view.ids, 'number_people_model_text'):
                count = len(self.selected_model.train_dataset_Y)
                self.view.ids.number_people_model_text.text = str(count)

            # Update person count
            if hasattr(self.view.ids, 'number_people_database_text'):
                count = len(person_service.get_all_persons())
                self.view.ids.number_people_database_text.text = str(count)

            if hasattr(self.view.ids, 'model_spinner'):
                logger.info("Updating model spinner values")
                self.view.ids.model_spinner.values = self.get_available_models()
                self.view.ids.model_spinner.text = self.get_selected_model_name()

            if hasattr(self.view.ids, 'model_spinner'):
                logger.info("Updating model spinner values")
                self.view.ids.model_spinner.values = self.get_available_models()
                self.view.ids.model_spinner.text = self.get_selected_model_name()
        except Exception as e:
            logger.exception("Error updating view")

    # ============================================================
    # Model Management
    # ============================================================

    def get_available_models(self) -> list:
        """Get all available model names."""
        try:
            models = model_service.get_all_models()
            return [m.name for m in models] if models else []
        except Exception as e:
            logger.exception("Error getting model names")
            return []

    def get_available_cameras(self) -> list:
        """Get all available model names."""
        try:
            return [f"Port {p}" for p in camera_service.get_all_cameras()]
        except Exception as e:
            logger.exception("Error getting model names")
            return []

    def get_selected_model_name(self) -> str:
        """Get currently selected model name."""
        return self.selected_model.name if self.selected_model else "No models"

    def get_selected_camera_port(self) -> str:
        """Get currently selected model name."""
        return f"Port {self.selected_camera}" if self.selected_camera is not None else "No cameras"

    def select_model(self, model_name: str) -> bool:
        """Select a model by name.

        Args:
            model_name: Name of model to select

        Returns:
            True if successful
        """
        try:
            model = model_service.get_model(model_name)
            if model:
                self.selected_model = model
                logger.info(f"Selected model: {model_name}")
                return True
            else:
                logger.warning(f"Model not found: {model_name}")
                return False

        except Exception as e:
            logger.exception(f"Error selecting model {model_name}")
            return False

    def select_camera(self, camera_port: str) -> bool:
        try:
            self.selected_camera = int(camera_port.split()[-1])
            return True
        except:
            return False

    def get_model_person_count(self) -> int:
        """Get number of persons in selected model."""
        if self.selected_model:
            return len(self.selected_model.train_dataset_Y)
        return 0

    # ============================================================
    # Statistics Management
    # ============================================================

    def record_identification(self, success: bool) -> None:
        """Record identification result.

        Args:
            success: True if correct, False if incorrect
        """
        try:
            hour = TimeUtils.get_hour()
            day = TimeUtils.get_day()
            month = TimeUtils.get_month()

            ok_val = 1 if success else 0
            nok_val = 0 if success else 1
            data = [hour, day, month, 0, ok_val, nok_val]

            with open(config.stats.FILE_STATS_CSV, "a", newline='') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(data)

            logger.info(f"Recorded identification: {'OK' if success else 'NOK'}")

        except Exception as e:
            logger.exception("Error recording identification")

    def record_attempt(self) -> None:
        """Record identification attempt."""
        try:
            hour = TimeUtils.get_hour()
            day = TimeUtils.get_day()
            month = TimeUtils.get_month()
            data = [hour, day, month, 1, 0, 0]

            with open(config.stats.FILE_STATS_CSV, "a", newline='') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(data)

        except Exception as e:
            logger.exception("Error recording attempt")

    def clear_statistics(self) -> None:
        """Clear statistics file."""
        try:
            current_hour = TimeUtils.get_hour()
            current_day = TimeUtils.get_day()
            current_month = TimeUtils.get_month()

            first_hour = (current_hour - 11) % 24
            range_hours = [(first_hour + i) % 24 for i in range(12)]

            with open(config.stats.FILE_STATS_CSV, "w", newline='') as f:
                writer = csv.writer(f, delimiter=',')
                for hour in range_hours:
                    day = current_day - 1 if hour > current_hour else current_day
                    data = [hour, day, current_month, 0, 0, 0]
                    writer.writerow(data)

            self._create_blank_plot()
            logger.info("Statistics cleared")

        except Exception as e:
            logger.exception("Error clearing statistics")

    # ============================================================
    # Plot Management
    # ============================================================

    def get_plot_path(self) -> str:
        """Generate and return plot image path."""
        try:
            data_csv = []
            if config.stats.FILE_STATS_CSV.exists():
                with open(config.stats.FILE_STATS_CSV, 'r') as f:
                    reader = csv.reader(f, delimiter=',')
                    for row in reader:
                        if row:
                            data_csv.append(row)

            if not data_csv:
                self._create_blank_plot()
                return str(config.stats.FILE_RESULT_PLOT)

            ok_y, nok_y, nnok_y, x = self._process_stats_data(data_csv)

            if x:
                self._create_plot(x, ok_y, nok_y, nnok_y)
            else:
                self._create_blank_plot()

            return str(config.stats.FILE_RESULT_PLOT)

        except Exception as e:
            logger.exception("Error getting plot")
            self._create_blank_plot()
            return str(config.stats.FILE_RESULT_PLOT)

    def _process_stats_data(self, data_csv: list) -> tuple:
        """Process statistics CSV data."""
        now = datetime.now()
        current_hour = now.hour

        first_hour = (current_hour - 11) % 24
        range_hours = [(first_hour + i) % 24 for i in range(12)]

        x, ok_y, nok_y, nnok_y = [], [], [], []

        for hour in range_hours:
            ok, nok, nnok = 0, 0, 0

            for element in data_csv:
                try:
                    if len(element) >= 6 and int(element[0]) == hour:
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
        """Create statistics plot."""
        try:
            series1 = np.array(ok_y)
            series2 = np.array(nok_y)
            series3 = np.array(nnok_y)

            index = np.arange(len(x))
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)')
            plt.ylabel('Count of identifications')
            plt.xlabel('Hour')

            plt.bar(index, series1, color="g", label="Correct")
            plt.bar(index, series2, color="r", bottom=series1, label="Incorrect")
            plt.bar(index, series3, color="b", bottom=(series2 + series1), label="No ID")

            plt.xticks(index, x)
            ax = plt.gca()
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis='y')
            plt.legend()

            plt.savefig(config.stats.FILE_RESULT_PLOT, dpi=80, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.exception("Error creating plot")

    def _create_blank_plot(self) -> None:
        """Create blank plot."""
        try:
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)')
            plt.ylabel('Count of identifications')
            plt.xlabel('Hour')
            plt.savefig(config.stats.FILE_RESULT_PLOT, dpi=80, bbox_inches='tight')
            plt.close()
        except Exception as e:
            logger.exception("Error creating blank plot")
