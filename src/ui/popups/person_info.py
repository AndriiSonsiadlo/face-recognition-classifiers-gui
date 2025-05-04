# Copyright (C) 2021 Andrii Sonsiadlo

import os

from kivy.clock import mainthread
from kivy.uix.popup import Popup

from Popup.plot_popup import PlotPopup
from core import config
from person.person import Person


class PersonInfoPopup(Popup):
    show_popup_person_info = 0

    def __init__(self, person: Person, **kwargs, ):
        super().__init__(**kwargs)
        self.current_person = person
        self.title = self.current_person.name
        self.set_person_info()
        self.preview_photo_index = 0

    def set_person_info(self):
        self.ids.person_name.text = self.current_person.name
        self.ids.person_age.text = str(self.current_person.age) or "N/A"
        self.ids.nationality.text = self.current_person.nationality or "N/A"
        self.ids.person_gender.text = self.current_person.gender or "N/A"
        self.ids.details.text = self.current_person.details or "N/A"
        self.ids.contact_phone.text = self.current_person.contact_phone or "N/A"

        self.show_preview_photo()

    @mainthread
    def show_preview_photo(self, photo_index=0):
        if len(self.current_person.photo_paths) > 0:
            image = self.current_person.photo_paths[photo_index]
            self.ids.preview_photo.source = image
            photo_name = os.path.basename(image)
            self.ids.preview_photo_name.text = photo_name + ' (' + str(photo_index + 1) + '/' + str(
                len(self.current_person.photo_paths)) + ')'
        else:
            self.delete_preview_photo()

    def delete_preview_photo(self):
        self.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
        self.ids.preview_photo_name.text = '(0/0)'

    def previous_photo(self):
        if not self.current_person is None:
            if self.preview_photo_index > 0:
                self.preview_photo_index -= 1
                self.show_preview_photo(self.preview_photo_index)

    def next_photo(self):
        if not self.current_person is None:
            if self.preview_photo_index < len(self.current_person.photo_paths) - 1:
                self.preview_photo_index += 1
                self.show_preview_photo(self.preview_photo_index)

    def popup_photo(self):
        if (self.current_person is not None) and (len(self.current_person.photo_paths)):
            try:
                popupWindow = PlotPopup(self.ids.preview_photo.source)
                popupWindow.open()
            except BaseException:
                popupWindow = PlotPopup(self.current_person.photo_paths[self.preview_photo_index])
                popupWindow.open()

    def ok_pressed(self):
        self.dismiss()
