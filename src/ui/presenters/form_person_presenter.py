import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import cv2
import dlib
from kivy.clock import mainthread

from core import config, AppLogger, Gender
from ui.presenters.base_presenter import BasePresenter
from utils.get_image_dimensions import get_crop_dims

logger = AppLogger().get_logger(__name__)


class FormPersonPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.photos = []
        self.preview_photo_index = 0
        self.is_edit_mode = False
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            logger.info("FormPersonPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing FormPersonPresenter")

    def start(self) -> None:
        try:
            logger.info("FormPersonPresenter started")
        except Exception as e:
            logger.exception("Error starting FormPersonPresenter")

    def stop(self) -> None:
        logger.info("FormPersonPresenter stopped")

    def refresh(self) -> None:
        try:
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing FormPersonPresenter")

    def _update_view(self) -> None:
        pass

    def set_edit_mode(self, is_edit: bool) -> None:
        self.is_edit_mode = is_edit
        logger.info(f"Form mode set to: {'EDIT' if is_edit else 'ADD'}")

    @mainthread
    def load_photos(self) -> None:
        logger.debug('load_photos(): button action "Choose photos"')

        num_loaded = self.require_photos()
        if num_loaded > 0:
            self.view.ids.num_files.text = f"{num_loaded} loaded"
            self.view.ids.num_files.opacity = 1
            self.view.ids.add_photo_icon.opacity = 0

        try:
            self.view.get_root_window().raise_window()
        except:
            pass

    def require_photos(self) -> int:
        root = tk.Tk()
        root.withdraw()

        photo_paths = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpeg *.jpg *.png *.bmp *.tiff")]
        )

        count_loaded = 0
        if photo_paths:
            logging.debug("require_photos(): Loading photos from file explorer")

            for img_path in photo_paths:
                img_lower = img_path.lower()
                if (img_lower.endswith(('.jpeg', '.jpg', '.png', '.bmp', '.tiff'))
                        and not img_lower.startswith("._")):

                    if self.is_edit_mode and hasattr(self.view, 'presenter'):
                        self.view.presenter.add_new_photos([img_path])
                    else:
                        self.photos.append(img_path)

            count_loaded = len(self.photos) + len(
                self.view.presenter.photos_to_add if self.is_edit_mode else []
            )
            if count_loaded > 0:
                self.show_preview_photo(index=self.preview_photo_index)

        return count_loaded

    def set_default_image(self) -> None:
        try:
            self.view.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
            self.view.ids.preview_photo_name.text = '(0/0)'
            self.view.ids.num_files.opacity = 0
            self.view.ids.add_photo_icon.opacity = 0.6
        except Exception as e:
            logger.exception("Error setting default image")

    def previous_photo(self) -> None:
        try:
            if self.preview_photo_index > 0:
                self.preview_photo_index -= 1
                self.show_preview_photo(self.preview_photo_index)
        except Exception as e:
            logger.exception("Error going to previous photo")

    def next_photo(self) -> None:
        try:
            all_photos = self._get_all_photos()
            if self.preview_photo_index < len(all_photos) - 1:
                self.preview_photo_index += 1
                self.show_preview_photo(self.preview_photo_index)
        except Exception as e:
            logger.exception("Error going to next photo")

    def delete_photo(self) -> None:
        try:
            all_photos = self._get_all_photos()
            if not all_photos:
                return

            deleted_path = all_photos[self.preview_photo_index]

            if self.is_edit_mode and hasattr(self.view, 'presenter'):
                self.view.presenter.delete_current_photo(deleted_path)
            else:
                if deleted_path in self.photos:
                    self.photos.remove(deleted_path)

            logger.info(f"Marked photo for deletion: {deleted_path}")

            all_photos = self._get_all_photos()
            if len(all_photos):
                self.view.ids.num_files.text = f"{len(all_photos)} loaded"
                if self.preview_photo_index >= len(all_photos):
                    self.preview_photo_index = len(all_photos) - 1
                self.show_preview_photo(index=self.preview_photo_index)
            else:
                self.set_default_image()

        except Exception as e:
            logger.exception("Error deleting photo")

    def _get_all_photos(self) -> list:
        all_photos = []

        if self.is_edit_mode and hasattr(self.view, 'presenter'):
            if self.view.presenter.current_person:
                existing = [
                    str(p) for p in self.view.presenter.current_person.photo_paths
                    if str(p) not in [str(x) for x in self.view.presenter.photos_to_delete]
                ]
                all_photos.extend(existing)
            all_photos.extend([str(p) for p in self.view.presenter.photos_to_add])
        else:
            all_photos = self.photos

        return all_photos

    @mainthread
    def show_preview_photo(self, index: int) -> None:
        try:
            all_photos = self._get_all_photos()

            if len(all_photos) > 0 and len(all_photos) > index:
                self.view.ids.count_face_text.opacity = 0

                image_path = str(all_photos[index])
                if os.path.exists(image_path):
                    self.view.ids.preview_photo.source = image_path
                else:
                    if self.is_edit_mode:
                        self.view.presenter.delete_current_photo(image_path)
                    else:
                        if image_path in self.photos:
                            self.photos.remove(image_path)
                    return

                photo_name = os.path.basename(image_path)
                self.view.ids.preview_photo_name.text = (
                    f"{photo_name} ({index + 1}/{len(all_photos)})"
                )
            else:
                self.set_default_image()
        except Exception as e:
            logger.exception("Error showing preview photo")

    def crop_photo(self) -> None:
        try:
            all_photos = self._get_all_photos()
            if not all_photos:
                self.show_error("Error", "No photo loaded")
                return

            image_path = str(self.view.ids.preview_photo.source)
            if not image_path or not os.path.exists(image_path):
                self.show_error("Error", "Photo not found")
                return

            filename = Path(image_path).name

            x, y, w, h = get_crop_dims(image_path)
            x, y, w, h = int(x), int(y), int(w), int(h)

            if image_path != '' and w != 0 and h != 0:
                if not image_path.startswith("._"):
                    out = filename

                    image = cv2.imread(image_path)
                    cropped = image[y:y + h, x:x + w]

                    crop_dir = config.paths.TEMP_DIR
                    crop_dir.mkdir(parents=True, exist_ok=True)
                    cropped_path = str(crop_dir / out)

                    if os.path.exists(cropped_path):
                        i = 1
                        base_name = Path(out).stem
                        suffix = Path(out).suffix
                        while True:
                            temp_cropped_path = str(crop_dir / f"{base_name}_crop_{i}{suffix}")
                            if not os.path.exists(temp_cropped_path):
                                cropped_path = temp_cropped_path
                                break
                            i += 1

                    cv2.imwrite(cropped_path, cropped)
                    logger.info(f"Saved cropped image to temp: {cropped_path}")

                    if self.is_edit_mode:
                        self.view.presenter.delete_current_photo(image_path)
                        self.view.presenter.add_new_photos([cropped_path])
                        logger.info(f"Marked original for deletion and added cropped version")
                    else:
                        if image_path in self.photos:
                            idx = self.photos.index(image_path)
                            self.photos[idx] = cropped_path

                    self.preview_photo_index = max(0, self.preview_photo_index)
                    self.show_preview_photo(self.preview_photo_index)
                    self.show_info("Success", "Photo cropped successfully")
                    logger.info(f"Crop operation completed")

                cv2.destroyAllWindows()
        except Exception as e:
            logger.exception("Error cropping photo")
            self.show_error("Error", f"Failed to crop photo: {str(e)}")

    def face_detection(self) -> None:
        try:
            all_photos = self._get_all_photos()
            if not all_photos or self.preview_photo_index >= len(all_photos):
                self.show_error("Error", "No photo loaded")
                return

            image_path = str(self.view.ids.preview_photo.source)
            if not os.path.exists(image_path):
                self.show_error("Error", "Photo not found")
                return

            detector = dlib.get_frontal_face_detector()
            image = cv2.imread(image_path)

            rects = detector(image, 1)

            self.view.ids.count_face_text.text = f"Number of faces found: {len(rects)}"
            self.view.ids.count_face_text.opacity = 1

            logger.info(f"Face detection: {len(rects)} faces found")
        except Exception as e:
            logger.exception("Error in face detection")
            self.show_error("Error", f"Face detection failed: {str(e)}")

    @mainthread
    def set_person_data(self, person) -> None:
        try:
            self.set_edit_mode(True)

            self.view.ids.name.text = person.name
            self.view.ids.age.text = str(person.age) if person.age else ''

            if person.gender == Gender.MALE:
                self.view.ids.gender_male.active = True
                self.view.ids.gender_female.active = False
            else:
                self.view.ids.gender_male.active = False
                self.view.ids.gender_female.active = True

            self.view.ids.nationality.text = person.nationality or ''
            self.view.ids.details.text = person.details or ''
            self.view.ids.contact_phone.text = person.contact_phone or ''

            self.photos = []
            self.preview_photo_index = 0

            if len(person.photo_paths):
                self.view.ids.num_files.text = f"{len(person.photo_paths)} loaded"
                self.view.ids.num_files.opacity = 1
                self.view.ids.add_photo_icon.opacity = 0
                self.show_preview_photo(index=0)
            else:
                self.set_default_image()

            logger.info(f"Loaded person data: {person.name}")
        except Exception as e:
            logger.exception(f"Error setting person data: {e}")

    @mainthread
    def clear_inputs(self) -> None:
        try:
            self.set_edit_mode(False)

            self.view.ids.name.text = ''
            self.view.ids.age.text = ''
            self.view.ids.gender_male.active = True
            self.view.ids.gender_female.active = False
            self.view.ids.nationality.text = ''
            self.view.ids.details.text = ''
            self.view.ids.contact_phone.text = ''

            self.photos.clear()
            self.preview_photo_index = 0
            self.set_default_image()

            self.view.ids.count_face_text.opacity = 0
            logger.info("Form inputs cleared")
        except Exception as e:
            logger.exception("Error clearing inputs")
