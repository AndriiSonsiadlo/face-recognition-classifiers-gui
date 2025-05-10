# Copyright (C) 2021 Andrii Sonsiadlo
import logging
import os
import re
import tkinter as tk
from tkinter import filedialog
from typing import Optional

import cv2
import dlib
from kivy.clock import mainthread
from kivy.properties import ObjectProperty

from Popup.my_popup_warn import MyPopupWarn
from classes.Popup.my_popup_info import MyPopupInfo
from classes.Popup.plot_popup import PlotPopup
from core import AppLogger, Gender, config
from functions.get_image_dimensions import get_crop_dims
from ui.base_screen import BaseScreen
from ui.presenters.edit_person_presenter import EditPersonPresenter
from ui.presenters.form_person_presenter import FormPersonPresenter

logger = AppLogger().get_logger(__name__)


class EditPerson(BaseScreen):
    person = ObjectProperty(None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.preview_photo_index = 0
        self.presenter: Optional['EditPersonPresenter'] = None
        self.form_presenter: Optional['FormPersonPresenter'] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize screen resources."""
        try:
            self.presenter = EditPersonPresenter(self)
            self.form_presenter= FormPersonPresenter(self)
            self.presenter.start()
            self.form_presenter.start()

            self.logger.info("EditPersonScreen initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing EditPersonScreen: {e}")
            self.show_error("Initialization Error", str(e))

    def good_edited(self, old_name):
        self.person.edit(old_name, self.old_count_photo)
        self.show_popup_info(title="Person's data have been edited")

        # chaching data of person in person_list
        person_old = self.person_list.find_first(self.name)
        person_old = self.person

        for filename in os.listdir(self.person.photo_dir):
            #			for path in self.person.photo_paths:
            print(os.path.join(self.person.photo_dir, filename))
            print(self.person.photo_paths)
            if not f"{self.person.photo_dir}/{filename}" in self.person.photo_paths:
                try:
                    os.remove(f"{self.person.photo_dir}/{filename}")
                except BaseException:
                    pass
                continue

        self.person_list.save_to_file()

        self.manager.transition.direction = "right"
        self.manager.current = 'persons'

    def cancel(self):
        self.manager.current = 'persons'
