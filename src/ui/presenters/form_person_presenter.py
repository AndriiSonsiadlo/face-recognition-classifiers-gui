import logging
import os
import tkinter as tk
from os import path
from pathlib import Path
from tkinter import filedialog

import cv2
import dlib
from kivy.clock import mainthread

from core import config, AppLogger, Gender
from functions.get_image_dimensions import get_crop_dims
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class FormPersonPresenter(BasePresenter):
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
            pass
        except Exception as e:
            logger.exception("Error updating view")

    @mainthread
    def load_photos(self):
        logger.debug('load_photos(): button action "Choose photos"')

        num_loaded = self.require_photos()
        if num_loaded > 0:
            self.view.ids.num_files.text = str(num_loaded) + " loaded"
            self.view.ids.num_files.opacity = 1
            self.view.ids.add_photo_icon.opacity = 0
        self.view.get_root_window().raise_window()  # set focus on window

    def require_photos(self):
        root = tk.Tk()
        root.withdraw()

        photo_paths = filedialog.askopenfilenames(
            filetypes=[("Image files", ".jpeg .jpg .png .bmp .tiff")])

        count_loaded = 0
        if photo_paths:
            logging.debug("get_photos(): Uploading photos from the explorer")

            for img_path in photo_paths:
                img_lower = img_path.lower()
                if img_lower.endswith(
                        ('.jpeg', '.jpg', '.png', '.bmp', '.tiff')) and not img_lower.startswith(
                    "._"):
                    self.photos.append(img_path)
            count_loaded = len(self.photos)
            if len(photo_paths) > 0:
                self.show_preview_photo(index=self.preview_photo_index)
        return count_loaded

    def set_default_image(self):
        self.view.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
        self.view.ids.preview_photo_name.text = '(0/0)'
        self.view.ids.num_files.opacity = 0
        self.view.ids.add_photo_icon.opacity = 0.6

    def previous_photo(self):
        if self.preview_photo_index > 0:
            self.preview_photo_index -= 1
            self.show_preview_photo(self.preview_photo_index)

    def next_photo(self):
        if self.preview_photo_index < len(self.photos) - 1:
            self.preview_photo_index += 1
            self.show_preview_photo(self.preview_photo_index)

    def delete_photo(self):
        if len(self.photos):
            self.photos.pop(self.preview_photo_index)
            if len(self.photos):
                self.view.ids.num_files.text = str(len(self.photos)) + " loaded"
                if self.preview_photo_index >= len(self.photos):
                    self.preview_photo_index = len(self.photos) - 1
                self.show_preview_photo(index=self.preview_photo_index)
            else:
                self.set_default_image()

    def show_preview_photo(self, index):
        if len(self.photos) > 0 and len(self.photos) > index:
            self.view.ids.count_face_text.opacity = 0

            image = self.photos[index]
            if os.path.exists(image):
                self.view.ids.preview_photo.source = str(image)
            else:
                self.photos.pop(index)
            photo_name = os.path.basename(image)
            self.view.ids.preview_photo_name.text = photo_name + ' (' + str(index + 1) + '/' + str(
                len(self.photos)) + ')'
        else:
            self.set_default_image()

    def crop_photo(self):
        if not self.photos:
            return

        crop_dir = config.paths.TEMP_DIR
        image_path = self.view.ids.preview_photo.source
        filename = Path(image_path).name

        x, y, w, h = get_crop_dims(self.view.ids.preview_photo.source)

        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)

        if image_path != '' and w != 0 and h != 0:
            if not image_path.startswith("._"):
                OutName = filename

                image = cv2.imread(image_path)
                cropped = image[y:y + h, x:x + w]

                cropped_path = f"{crop_dir}/{OutName}"
                # write the cropped image to disk
                if path.exists(cropped_path):
                    while True:
                        i = 1
                        temp_cropped_path = f"{cropped_path}_{i}"
                        if path.exists(temp_cropped_path):
                            i += 1
                        else:
                            cropped_path = temp_cropped_path
                            break

                cv2.imwrite(cropped_path, cropped)
                self.photos[self.preview_photo_index] = cropped_path
                self.show_preview_photo(self.preview_photo_index)

            cv2.destroyAllWindows()

    def face_detection(self):
        image_path = self.view.ids.preview_photo.source
        if self.photos:
            detector = dlib.get_frontal_face_detector()
            image = cv2.imread(image_path)
            rects = detector(image, 1)
            self.view.ids.count_face_text.text = str(f"Number of faces found: {len(rects)}")
            self.view.ids.count_face_text.opacity = 1

    @mainthread
    def set_person_data(self, person):
        self.view.ids.create_person_name.text = person.name
        self.view.ids.create_person_age.text = str(person.age)
        if person.gender == Gender.MALE:
            self.view.ids.create_person_gender_male.active = True
            self.view.ids.create_person_gender_female.active = False
        else:
            self.view.ids.create_person_gender_male.active = False
            self.view.ids.create_person_gender_female.active = True

        self.view.ids.create_person_nationality.text = person.nationality
        self.view.ids.create_person_details.text = person.details
        self.view.ids.create_contact_phone.text = person.contact_phone

        if len(person.photo_paths):
            self.view.ids.num_files.text = str(len(person.photo_paths)) + " loaded"
            self.view.ids.num_files.opacity = 1
            self.view.ids.add_photo_icon.opacity = 0
        else:
            self.view.ids.preview_photo_name.text = '(0/0)'
            self.view.ids.num_files.opacity = 0
            self.view.ids.add_photo_icon.opacity = 0.6

        self.photos = person.photo_paths
        self.view.form_presenter.show_preview_photo(index=self.preview_photo_index)

    @mainthread
    def clear_inputs(self):
        logger.debug('clear_inputs(): clearing all ui-field in a screen')

        self.view.ids.create_person_name.text = ''
        self.view.ids.create_person_age.text = ''
        self.view.ids.gender_male.active = True
        self.view.ids.create_person_nationality.text = ''
        self.view.ids.create_person_details.text = ''
        self.view.ids.create_contact_phone.text = ''

        self.photos.clear()
        self.view.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
        self.view.ids.preview_photo_name.text = '(0/0)'
        self.view.ids.num_files.opacity = 0
        self.view.ids.add_photo_icon.opacity = 0.6

        self.view.ids.count_face_text.opacity = 0
