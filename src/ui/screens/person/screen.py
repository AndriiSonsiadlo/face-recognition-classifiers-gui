import os
from typing import Optional

from kivy.clock import mainthread

from core import config, AppLogger
from models.person.person_metadata import PersonMetadata
from services import person_service
from ui.base_screen import BaseScreen
from ui.presenters.persons_presenter import PersonsPresenter

logger = AppLogger().get_logger(__name__)


class PersonsScreen(BaseScreen):
    screen = None

    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)
        PersonsScreen.screen = self

        self.presenter: Optional['PersonsPresenter'] = None
        self.preview_photo_index = 0
        self._initialize()

    def _initialize(self) -> None:
        try:
            self.presenter = PersonsPresenter(self)
            self.presenter.start()
            logger.info("PersonsScreen initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing PersonsScreen: {e}")
            self.show_error("Initialization Error", str(e))

    def set_person_info(self, person: PersonMetadata) -> None:
        try:
            self.preview_photo_index = 0
            self.presenter.selected_person = person

            self._update_person_display(person)
            self._update_photo_display()
        except Exception as e:
            self.logger.exception(f"Error setting person info: {e}")
            self.show_error("Error", str(e))

    def _update_person_display(self, person: PersonMetadata) -> None:
        try:
            self.ids.name.text = person.name or 'Unknown'
            self.ids.age.text = str(person.age) if person.age else 'N/A'
            self.ids.nationality.text = person.nationality or 'N/A'
            self.ids.gender.text = person.gender.value if person.gender else 'N/A'
            self.ids.details.text = person.details or 'N/A'
            self.ids.contact_phone.text = person.contact_phone or 'N/A'
        except Exception as e:
            self.logger.exception("Error updating person display")

    def clear_person_info(self) -> None:
        try:
            self.ids.name.text = ''
            self.ids.age.text = ''
            self.ids.gender.text = ''
            self.ids.nationality.text = ''
            self.ids.details.text = ''
            self.ids.contact_phone.text = ''
            self.preview_photo_index = 0
            self._delete_preview_photo()
        except Exception as e:
            self.logger.exception("Error clearing person info")

    @mainthread
    def _update_photo_display(self) -> None:
        try:
            if not self.presenter or not self.presenter.selected_person:
                self._delete_preview_photo()
                return

            person = self.presenter.selected_person

            if not person.photos_path.exists():
                self._delete_preview_photo()
                return

            if len(person.photo_paths) > 0:
                self._show_preview_photo(self.preview_photo_index)
            else:
                self._delete_preview_photo()
        except Exception as e:
            self.logger.exception("Error updating photo display")

    @mainthread
    def _show_preview_photo(self, photo_index: int = 0) -> None:
        try:
            if not self.presenter or not self.presenter.selected_person:
                return

            person = self.presenter.selected_person
            if len(person.photo_paths) == 0:
                self._delete_preview_photo()
                return

            photo_index = max(0, min(photo_index, len(person.photo_paths) - 1))

            image = person.photo_paths[photo_index]
            if os.path.exists(str(image)):
                self.ids.preview_photo.source = str(image)
            else:
                self._delete_preview_photo()
                return

            photo_name = os.path.basename(str(image))
            self.ids.preview_photo_name.text = (
                f"{photo_name} ({photo_index + 1}/{len(person.photo_paths)})"
            )

            if len(person.photo_paths) == 1:
                self._disable_button(self.ids.previous_photo_btn)
                self._disable_button(self.ids.next_photo_btn)
            else:
                self._enable_button(self.ids.previous_photo_btn)
                self._enable_button(self.ids.next_photo_btn)

        except Exception as e:
            self.logger.exception("Error showing preview photo")

    def _delete_preview_photo(self) -> None:
        try:
            self.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
            self.ids.preview_photo_name.text = '(0/0)'
            self._disable_button(self.ids.previous_photo_btn)
            self._disable_button(self.ids.next_photo_btn)
        except Exception as e:
            self.logger.exception("Error deleting preview photo")

    def previous_photo(self) -> None:
        try:
            if self.preview_photo_index > 0:
                self.preview_photo_index -= 1
                self._show_preview_photo(self.preview_photo_index)
        except Exception as e:
            self.logger.exception("Error going to previous photo")

    def next_photo(self) -> None:
        try:
            if self.presenter and self.presenter.selected_person:
                person = self.presenter.selected_person
                if self.preview_photo_index < len(person.photo_paths) - 1:
                    self.preview_photo_index += 1
                    self._show_preview_photo(self.preview_photo_index)
        except Exception as e:
            self.logger.exception("Error going to next photo")

    def popup_photo(self) -> None:
        try:
            if (self.presenter and self.presenter.selected_person and
                    len(self.presenter.selected_person.photo_paths)):
                try:
                    from ui.popups.plot import PlotPopup
                    popup_window = PlotPopup(self.ids.preview_photo.source)
                    popup_window.open()
                except Exception as e:
                    photo_path = self.presenter.selected_person.photo_paths[
                        self.preview_photo_index]
                    from ui.popups.plot import PlotPopup
                    popup_window = PlotPopup(str(photo_path))
                    popup_window.open()
        except Exception as e:
            self.logger.exception("Error showing photo popup")

    def add_person_action(self) -> None:
        try:
            self.manager.transition.direction = "left"
            self.manager.current = "add_person"
        except Exception as e:
            self.logger.exception("Error navigating to add person")

    def edit_person(self) -> None:
        try:
            selected = self.ids.rv.get_selected()
            if selected is None:
                self.show_error("Error", "Please select a person to edit")
                return

            if not self.presenter or not self.presenter.selected_person:
                self.show_error("Error", "No person selected")
                return

            edit_screen = self.manager.get_screen("edit_person")
            edit_screen.person = self.presenter.selected_person

            self.manager.transition.direction = "left"
            self.manager.current = "edit_person"

            logger.info(f"Editing person: {self.presenter.selected_person.name}")
        except Exception as e:
            self.logger.exception("Error editing person")
            self.show_error("Error", str(e))

    def delete_person(self) -> None:
        try:
            selected = self.ids.rv.get_selected()
            if selected is None:
                self.show_error("Error", "Please select a person to delete")
                return

            if not self.presenter or not self.presenter.selected_person:
                self.show_error("Error", "No person selected")
                return

            from ui.popups.delete import DeletePersonPopup
            popup = DeletePersonPopup(self.presenter.selected_person.name)
            popup.bind(on_dismiss=self._on_person_deleted)
            popup.open()

        except Exception as e:
            self.logger.exception("Error deleting person")
            self.show_error("Error", str(e))

    def _on_person_deleted(self, instance) -> None:
        try:
            self._select_person_by_index(0)
            self.refresh()
        except Exception as e:
            self.logger.exception("Error on person deleted")

    def refresh(self) -> None:
        try:
            person_service.refresh()
            if self.presenter:
                self.presenter.refresh()

            persons = person_service.get_all_persons()
            if persons:
                self.presenter.refresh_recyclerview(persons)
                if not self.presenter.selected_person:
                    self._select_person_by_index(0)
            else:
                self.presenter.empty_recyclerview()

            logger.info("PersonsScreen refreshed")
        except Exception as e:
            self.logger.exception("Error refreshing PersonsScreen")

    def _select_person_by_index(self, index: int) -> None:
        try:
            if hasattr(self.ids, 'rv_box') and hasattr(self.ids, 'rv'):
                self.ids.rv_box.select_node(None)
                self.ids.rv_box.select_node(index)

                if index < len(self.ids.rv.data):
                    person_data = self.ids.rv.data[index]
                    if 'person' in person_data:
                        self.set_person_info(person_data['person'])
                        logger.info(f"Selected person at index {index}")

        except Exception as e:
            self.logger.exception(f"Error selecting person by index: {e}")

    def _disable_button(self, button) -> None:
        try:
            button.disabled = True
            button.opacity = 0.5
        except Exception as e:
            self.logger.exception("Error disabling button")

    def _enable_button(self, button) -> None:
        try:
            button.disabled = False
            button.opacity = 1.0
        except Exception as e:
            self.logger.exception("Error enabling button")
