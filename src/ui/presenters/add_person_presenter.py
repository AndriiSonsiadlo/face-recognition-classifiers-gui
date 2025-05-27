import logging

from core import AppLogger, Gender
from models.person.person_metadata import PersonMetadata
from services import person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class AddPersonPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            logger.info("AddPersonPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing PersonsPresenter")

    def start(self) -> None:
        try:
            self._update_view()
            logger.info("PersonsPresenter started")
        except Exception as e:
            logger.exception("Error starting PersonsPresenter")

    def stop(self) -> None:
        logger.info("PersonsPresenter stopped")

    def refresh(self) -> None:
        try:
            person_service.refresh()
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing PersonsPresenter")

    def _update_view(self) -> None:
        try:
            self.view.form_presenter.clear_inputs()
        except Exception as e:
            logger.exception("Error updating view")

    def add_person(self):
        logging.debug('add_person(): init data of person')

        try:
            new = PersonMetadata(
                name=self.view.ids.name.text,
                age=self.view.ids.age.text,
                gender=(Gender.MALE if self.view.ids.gender_male.active == True else Gender.FEMALE),
                nationality=self.view.ids.nationality.text,
                details=self.view.ids.details.text,
                contact_phone=self.view.ids.contact_phone.text,
            )
        except Exception as e:
            self.show_error(title="Validation error", message=str(e))
            return

        if person_service.get_person(new.name):
            self.show_error(title="Error",
                            message=f"The person {new.name} already exists in database")
            return

        try:
            created = person_service.create_person(new, photo_paths=self.view.form_presenter.photos)
            if created:
                self.view.form_presenter.clear_inputs()
                self.show_info(title="Success", message="Person has been added to a registry")
            else:
                self.show_error(title="Error", message="Person hasn't been added to a registry")
        except Exception as e:
            logger.exception(f"Error adding person {new.name}: {e}")
            self.show_error(title="Error", message=str(e))
