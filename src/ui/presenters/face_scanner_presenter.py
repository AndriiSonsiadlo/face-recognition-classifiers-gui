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
    def __init__(self, view):
        super().__init__(view)
        self.selected_camera = None
        self.selected_model = None
        self._initialize_data()

    def _initialize_data(self) -> None:
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
        try:
            self._update_view()
            logger.info("FaceScannerPresenter started")
        except Exception as e:
            logger.exception("Error starting FaceScannerPresenter")

    def stop(self) -> None:
        logger.info("FaceScannerPresenter stopped")

    def refresh(self) -> None:
        try:
            model_service.refresh()
            person_service.refresh()
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing FaceScannerPresenter")

    def _update_view(self) -> None:
        try:
            models = self.get_available_models()
            if not self.selected_model or self.selected_model and self.selected_model.name is not models:
                if models:
                    self.select_model(models[0])
                else:
                    self.selected_model = None

            if self.selected_model and hasattr(self.view.ids, 'number_people_model_text'):
                count = len(self.selected_model.train_dataset_Y)
                self.view.ids.number_people_model_text.text = str(count)

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

    def get_available_models(self) -> list:
        try:
            models = model_service.get_all_models()
            return [m.name for m in models] if models else []
        except Exception as e:
            logger.exception("Error getting model names")
            return []

    def get_available_cameras(self) -> list:
        try:
            return [f"Port {p}" for p in camera_service.get_all_cameras()]
        except Exception as e:
            logger.exception("Error getting model names")
            return []

    def get_selected_model_name(self) -> str:
        return self.selected_model.name if self.selected_model else "No models"

    def get_selected_camera_port(self) -> str:
        return f"Port {self.selected_camera}" if self.selected_camera is not None else "No cameras"

    def select_model(self, model_name: str) -> bool:
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
        if self.selected_model:
            return len(self.selected_model.train_dataset_Y)
        return 0

    def record_identification(self, success: bool) -> None:
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

    def get_plot_path(self) -> str:
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

            ok_y, nok_y, no_id_y, x = self._process_stats_data(data_csv)

            if x:
                self._create_plot(x, ok_y, nok_y, no_id_y)
            else:
                self._create_blank_plot()

            return str(config.stats.FILE_RESULT_PLOT)

        except Exception as e:
            logger.exception("Error getting plot")
            self._create_blank_plot()
            return str(config.stats.FILE_RESULT_PLOT)

    def _process_stats_data(self, data_csv: list) -> tuple:
        now = datetime.now()
        current_hour = now.hour

        first_hour = (current_hour - 11) % 24
        range_hours = [(first_hour + i) % 24 for i in range(12)]

        x, ok_y, nok_y, no_id_y = [], [], [], []

        for hour in range_hours:
            ok, nok, no_id = 0, 0, 0

            for element in data_csv:
                try:
                    if len(element) >= 6 and int(element[0]) == hour:
                        no_id += int(element[3])
                        ok += int(element[4])
                        nok += int(element[5])
                except (ValueError, IndexError):
                    continue

            x.append(hour)
            ok_y.append(ok)
            nok_y.append(nok)
            no_id_y.append(no_id)

        return ok_y, nok_y, no_id_y, x

    def _create_plot(self, x: list, ok_y: list, nok_y: list, no_id_y: list) -> None:
        try:
            series_ok = np.array(ok_y)
            series_nok = np.array(nok_y)
            series_no_id = np.array(no_id_y)

            index = np.arange(len(x))
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)', fontsize=14, fontweight='bold')
            plt.ylabel('Count of identifications', fontsize=11)
            plt.xlabel('Hour', fontsize=11)

            color_correct = "#A8E6CF"
            color_incorrect = "#FFB3BA"
            color_no_id = "#BAD7FF"

            plt.bar(index, series_ok, color=color_correct, label="Correct", edgecolor='white', linewidth=1)
            plt.bar(index, series_nok, color=color_incorrect, bottom=series_ok, label="Incorrect", edgecolor='white', linewidth=1)
            plt.bar(index, series_no_id, color=color_no_id, bottom=(series_ok + series_nok), label="No ID", edgecolor='white', linewidth=1)

            plt.xticks(index, x)
            ax = plt.gca()
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(axis='y', alpha=0.4, linestyle='--')
            ax.set_facecolor('#F8F9FA')

            plt.legend(loc='upper left', framealpha=0.9)
            plt.tight_layout()

            plt.savefig(config.stats.FILE_RESULT_PLOT, dpi=100, bbox_inches='tight', facecolor='white')
            plt.close()

        except Exception as e:
            logger.exception("Error creating plot")

    def _create_blank_plot(self) -> None:
        try:
            plt.figure(figsize=(10, 6))
            plt.title('Result of identification (per hour)', fontsize=14, fontweight='bold')
            plt.ylabel('Count of identifications', fontsize=11)
            plt.xlabel('Hour', fontsize=11)

            ax = plt.gca()
            ax.set_facecolor('#F8F9FA')
            ax.grid(axis='y', alpha=0.4, linestyle='--')

            plt.tight_layout()
            plt.savefig(config.stats.FILE_RESULT_PLOT, dpi=100, bbox_inches='tight', facecolor='white')
            plt.close()
        except Exception as e:
            logger.exception("Error creating blank plot")
