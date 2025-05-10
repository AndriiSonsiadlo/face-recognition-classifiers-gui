from typing import Optional

from core import AppLogger
from ui.base_screen import BaseScreen
from ui.presenters.add_person_presenter import AddPersonPresenter
from ui.presenters.form_person_presenter import FormPersonPresenter

logger = AppLogger().get_logger(__name__)


class AddPerson(BaseScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.presenter: Optional['AddPersonPresenter'] = None
        self.form_presenter: Optional['FormPersonPresenter'] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize screen resources."""
        try:
            self.presenter = AddPersonPresenter(self)
            self.presenter.start()
            self.form_presenter= FormPersonPresenter(self)
            self.form_presenter.start()

            self.logger.info("AddPersonScreen initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing AddPersonScreen: {e}")
            self.show_error("Initialization Error", str(e))
