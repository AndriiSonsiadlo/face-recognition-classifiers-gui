from core import AppLogger, Gender
from services import person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class EditPersonPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.photos = []
        self.preview_photo_index = 0
        self._initialize_data()

    def _initialize_data(self) -> None:
        """Initialize data from registries."""
        try:
            logger.info("AddPersonPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing PersonsPresenter")

    def start(self) -> None:
        """Start presenter operations."""
        try:
            self._update_view()
            logger.info("PersonsPresenter started")
        except Exception as e:
            logger.exception("Error starting PersonsPresenter")

    def stop(self) -> None:
        """Stop presenter operations."""
        logger.info("PersonsPresenter stopped")

    def refresh(self) -> None:
        """Refresh data and UI."""
        try:
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing PersonsPresenter")

    def _update_view(self) -> None:
        """Update view with current data."""
        try:
            if self.view.person:
                self.view.form_presenter.set_person_data(person=self.view.person)
        except Exception as e:
            logger.exception("Error updating view")

    def update_person(self):
        new_name = self.view.ids.create_person_name.text
        if person_service.get_person(new_name):
            self.show_error(title="Error",
                            message=f"The person {new_name} already exists in database")
            return

        try:
            person_service.update_person(
                self.view.person.name,
                new_name=new_name,
                age=self.view.ids.create_person_age.text,
                gender=(
                    Gender.MALE if self.view.ids.create_person_gender_male.active == True else Gender.FEMALE),
                nationality=self.view.ids.create_person_nationality.text,
                details=self.view.ids.create_person_details.text,
                contact_phone=self.view.ids.create_contact_phone.text
            )



        except ValueError as e:
            self.show_error(title="Error while updating", message=str(e))
            return

        self.view.manager.transition.direction = "right"
        self.view.manager.current = 'persons'
