from typing import Optional

from kivy.properties import ObjectProperty

from core import AppLogger
from ui.base_screen import BaseScreen
from ui.presenters.edit_person_presenter import EditPersonPresenter
from ui.presenters.form_person_presenter import FormPersonPresenter

logger = AppLogger().get_logger(__name__)


class EditPerson(BaseScreen):
    person = ObjectProperty(None, allow_none=True)

    def __init__(self, **kw):
        super().__init__(__name__, **kw)
        self.presenter: Optional['EditPersonPresenter'] = None
        self.form_presenter: Optional['FormPersonPresenter'] = None
        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = EditPersonPresenter(self)
            self.form_presenter = FormPersonPresenter(self)

            self.form_presenter.view = self
            self.presenter.view = self

            self.presenter.start()
            self.form_presenter.start()

            self.logger.info("EditPersonScreen initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing EditPersonScreen: {e}")
            self.show_error("Initialization Error", str(e))

    def refresh(self) -> None:
        try:
            if self.person and self.presenter:
                self.presenter.set_person(self.person)
            super().refresh()
        except Exception as e:
            self.logger.exception(f"Error refreshing EditPerson: {e}")

    def on_pre_enter(self) -> None:
        try:
            self.refresh()
        except Exception as e:
            self.logger.exception("Error on_pre_enter")

    def on_leave(self) -> None:
        try:
            if self.presenter:
                self.presenter.stop()
            if self.form_presenter:
                self.form_presenter.stop()
            self.logger.info("EditPerson screen left")
        except Exception as e:
            self.logger.exception("Error on_leave")

    def add_photos(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.load_photos()
        except Exception as e:
            self.logger.exception("Error adding photos")

    def delete_photo(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.delete_photo()
        except Exception as e:
            self.logger.exception("Error deleting photo")

    def crop_photo(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.crop_photo()
        except Exception as e:
            self.logger.exception("Error cropping photo")

    def face_detection(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.face_detection()
        except Exception as e:
            self.logger.exception("Error detecting faces")

    def previous_photo(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.previous_photo()
        except Exception as e:
            self.logger.exception("Error showing previous photo")

    def next_photo(self) -> None:
        try:
            if self.form_presenter:
                self.form_presenter.next_photo()
        except Exception as e:
            self.logger.exception("Error showing next photo")

    def save_changes(self) -> None:
        try:
            if not self.presenter:
                self.show_error("Error", "Presenter not initialized")
                return

            success = self.presenter.update_person()
            if success:
                from services import person_service
                person_service.refresh()

                self._navigate_back()

                self.logger.info("Changes saved and persons screen refreshed")
            else:
                self.logger.warning("Person update failed")

        except Exception as e:
            self.logger.exception(f"Error saving changes: {e}")
            self.show_error("Error", f"Failed to save changes: {str(e)}")

    def cancel_edit(self) -> None:
        try:
            if self.presenter:
                self.presenter.photos_to_add.clear()
                self.presenter.photos_to_delete.clear()

            self._navigate_back()
        except Exception as e:
            self.logger.exception("Error canceling edit")

    def delete_current_person(self) -> None:
        try:
            if not self.presenter:
                self.show_error("Error", "Presenter not initialized")
                return

            from ui.popups.delete import DeletePersonPopup
            popup = DeletePersonPopup(self.person.name)
            popup.bind(on_dismiss=self._on_delete_dismissed)
            popup.open()
        except Exception as e:
            self.logger.exception(f"Error deleting person: {e}")
            self.show_error("Error", str(e))

    def _on_delete_dismissed(self, instance) -> None:
        try:
            from services import person_service
            person_service.refresh()

            self._navigate_back()
        except Exception as e:
            self.logger.exception("Error on delete dismissed")

    def _navigate_back(self) -> None:
        try:
            self.manager.transition.direction = "right"
            self.manager.current = "persons"
        except Exception as e:
            self.logger.exception("Error navigating back")
