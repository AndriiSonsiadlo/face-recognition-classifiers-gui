from typing import Optional

from core import AppLogger
from ui.base_screen import BaseScreen
from ui.presenters.learning_create_presenter import LearningCreatePresenter

logger = AppLogger().get_logger(__name__)


class LearningCreate(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)
        self.presenter: Optional['LearningCreatePresenter'] = None
        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = LearningCreatePresenter(self)
            self.presenter.start()
            logger.info("LearningCreate initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing LearningCreate: {e}")
            self.show_error("Initialization Error", str(e))

    def on_pre_enter(self) -> None:
        try:
            self.clear_inputs()
        except Exception as e:
            self.logger.exception("Error on_pre_enter")

    def get_algorithms(self):
        if self.presenter:
            return self.presenter.get_algorithms()
        return []

    def get_weights(self):
        if self.presenter:
            return self.presenter.get_weights()
        return []

    def get_gammas(self):
        if self.presenter:
            return self.presenter.get_gammas()
        return []

    def on_algorithm_selected(self, algorithm_name: str) -> None:
        try:
            if self.presenter:
                self.presenter.select_algorithm(algorithm_name)
        except Exception as e:
            self.logger.exception("Error selecting algorithm")

    def on_weight_selected(self, weight: str) -> None:
        try:
            if self.presenter:
                self.presenter.on_weight_selected(weight)
        except Exception as e:
            self.logger.exception("Error selecting weight")

    def on_gamma_selected(self, gamma: str) -> None:
        try:
            if self.presenter:
                self.presenter.on_gamma_selected(gamma)
        except Exception as e:
            self.logger.exception("Error selecting gamma")

    def on_neighbor_checkbox_changed(self, is_active: bool) -> None:
        try:
            if self.presenter:
                self.presenter.on_neighbor_checkbox_active(is_active)
        except Exception as e:
            self.logger.exception("Error handling checkbox change")

    def on_neighbor_input_changed(self, value: str) -> None:
        try:
            if self.presenter:
                self.presenter.set_n_neighbors(value)
        except Exception as e:
            self.logger.exception("Error setting neighbors")

    def enable_input(self, enabled: bool) -> None:
        try:
            if hasattr(self.ids, 'create_neighbor_num'):
                self.ids.create_neighbor_num.disabled = not enabled
                if not enabled:
                    self.ids.create_neighbor_num.text = ""
        except Exception as e:
            self.logger.exception("Error enabling input")

    def begin_training(self) -> None:
        try:
            if not self.presenter:
                self.show_error("Error", "Presenter not initialized")
                return

            self.presenter.begin_training()

        except Exception as e:
            self.logger.exception("Error starting training")
            self.show_error("Error", str(e))

    def search_persons(self, query: str) -> None:
        try:
            if self.presenter:
                self.presenter.search_persons(query)
        except Exception as e:
            self.logger.exception("Error searching persons")

    def clear_inputs(self) -> None:
        try:
            if self.presenter:
                self.presenter.clear_inputs()
        except Exception as e:
            self.logger.exception("Error clearing inputs")

    def go_back_to_learning(self) -> None:
        try:
            self.manager.transition.direction = "right"
            self.manager.current = "learning"
        except Exception as e:
            self.logger.exception("Error navigating back")

    def on_leave(self) -> None:
        try:
            if self.presenter:
                self.presenter.stop()
            logger.info("LearningCreate screen left")
        except Exception as e:
            self.logger.exception("Error on_leave")
