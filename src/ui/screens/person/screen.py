import os
import shutil
from typing import Optional

from kivy.clock import mainthread

from Popup.my_popup_ask import MyPopupAskPerson
from classes.Popup.plot_popup import PlotPopup
from core import config, AppLogger
from person.person import Person
from ui.base_screen import BaseScreen
from ui.presenters.persons_presenter import PersonsPresenter

logger = AppLogger().get_logger(__name__)


class PersonsScreen(BaseScreen):
    preview_photo_index = 0
    screen = None

    def __init__(self, **kwargs):
        super().__init__(__name__, **kwargs)
        PersonsScreen.screen = self

        self.presenter: Optional['PersonsPresenter'] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize screen resources."""
        try:
            self.presenter = PersonsPresenter(self)
            self.presenter.start()

            logger.info("PersonsScreen initialized successfully")

        except Exception as e:
            logger.exception(f"Error initializing PersonsScreen: {e}")
            self.show_error("Initialization Error", str(e))

    def set_person_info(self, person: Person):
        self.preview_photo_index = 0
        self.presenter.selected_person = person

        self.ids.person_name.text = self.presenter.selected_person.name
        self.ids.person_age.text = str(self.presenter.selected_person.age) or "N/A"
        self.ids.nationality.text = self.presenter.selected_person.nationality or "N/A"
        self.ids.person_gender.text = self.presenter.selected_person.gender or "N/A"
        self.ids.details.text = self.presenter.selected_person.details or "N/A"
        self.ids.contact_phone.text = self.presenter.selected_person.contact_phone or "N/A"

        self.show_preview_photo()

    def clear_person_info(self):
        self.ids.person_name.text = ''
        self.ids.person_age.text = ''
        self.ids.person_gender.text = ''
        self.ids.nationality.text = ''
        self.ids.details.text = ''
        self.ids.contact_phone.text = ''

        self.delete_preview_photo()

    @mainthread
    def show_preview_photo(self, photo_index=0):
        if len(self.presenter.selected_person.photo_paths) > 0:
            image = self.presenter.selected_person.photo_paths[photo_index]
            self.ids.preview_photo.source = str(image)
            photo_name = os.path.basename(image)
            self.ids.preview_photo_name.text = photo_name + ' (' + str(photo_index + 1) + '/' + str(
                len(self.presenter.selected_person.photo_paths)) + ')'

            if (len(self.presenter.selected_person.photo_paths)) == 1:
                self.disable_button(self.ids.previous_photo_btn)
                self.disable_button(self.ids.next_photo_btn)
            else:
                self.enable_button(self.ids.previous_photo_btn)
                self.enable_button(self.ids.next_photo_btn)
        else:
            self.disable_button(self.ids.previous_photo_btn)
            self.disable_button(self.ids.next_photo_btn)
            self.delete_preview_photo()

    def delete_preview_photo(self):
        self.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
        self.ids.preview_photo_name.text = '(0/0)'

    def disable_button(self, button):
        button.disabled = True
        button.opacity = .5

    def enable_button(self, button):
        button.disabled = False
        button.opacity = 1

    def previous_photo(self):
        if self.presenter.selected_person is not None:
            if self.preview_photo_index > 0:
                self.preview_photo_index -= 1
                self.show_preview_photo(self.preview_photo_index)

    def next_photo(self):
        if self.presenter.selected_person is not None:
            if self.preview_photo_index < len(self.presenter.selected_person.photo_paths) - 1:
                self.preview_photo_index += 1
                self.show_preview_photo(self.preview_photo_index)

    def popup_photo(self):
        if (self.presenter.selected_person is not None) and (
        len(self.presenter.selected_person.photo_paths)):
            try:
                popup_window = PlotPopup(self.ids.preview_photo.source)
                popup_window.open()
            except BaseException:
                popup_window = PlotPopup(
                    self.presenter.selected_person.photo_paths[self.preview_photo_index])
                popup_window.open()

    def delete_person(self):
        selected = self.person_list.get_selected()
        if selected is not None:
            popup_window = MyPopupAskPerson()
            del self.presenter.selected_person
            popup_window.bind(on_dismiss=self.popup_refresh)
            popup_window.open()
        else:
            print("No selected element")

    def open_screen_add(self):
        self.manager.transition.direction = "left"
        self.manager.current = "add_person"

    def open_screen_edit(self, person):
        edit_screen = self.manager.get_screen("edit_person")
        edit_screen.person = person
        self.manager.transition.direction = "left"
        self.manager.current = "edit_person"

    def edit_person(self):
        selected = self.ids.rv.get_selected()
        if selected is not None:
            self.open_screen_edit(self.presenter.selected_person)
        else:
            print("No selected element")

    def popup_refresh(self, instance):  # update screen after pressing delete
        self.refresh()
