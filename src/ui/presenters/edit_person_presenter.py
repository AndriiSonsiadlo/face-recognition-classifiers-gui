from pathlib import Path
from typing import Optional, List
import shutil

from core import AppLogger, Gender
from models.person.person_metadata import PersonMetadata
from services import person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class EditPersonPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.current_person: Optional[PersonMetadata] = None
        self.original_name: Optional[str] = None
        self.photos_to_add: List[str] = []
        self.photos_to_delete: List[str] = []
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            person_service.refresh()
            logger.info("EditPersonPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing EditPersonPresenter")

    def start(self) -> None:
        try:
            self._update_view()
            logger.info("EditPersonPresenter started")
        except Exception as e:
            logger.exception("Error starting EditPersonPresenter")

    def stop(self) -> None:
        logger.info("EditPersonPresenter stopped")

    def refresh(self) -> None:
        try:
            person_service.refresh()
            self._update_view()
        except Exception as e:
            logger.exception("Error refreshing EditPersonPresenter")

    def _update_view(self) -> None:
        try:
            if self.view.person and self.view.form_presenter:
                self.current_person = self.view.person
                self.original_name = self.view.person.name
                self.photos_to_add.clear()
                self.photos_to_delete.clear()
                self.view.form_presenter.set_person_data(person=self.view.person)
        except Exception as e:
            logger.exception("Error updating view")

    def set_person(self, person: PersonMetadata) -> None:
        try:
            self.current_person = person
            self.original_name = person.name
            self.photos_to_add.clear()
            self.photos_to_delete.clear()

            if self.view.form_presenter:
                self.view.form_presenter.set_person_data(person=person)

            logger.info(f"Set person for editing: {person.name}")
        except Exception as e:
            logger.exception(f"Error setting person: {e}")

    def add_new_photos(self, photo_paths: List[str]) -> bool:
        try:
            if not photo_paths:
                return False

            valid_photos = [p for p in photo_paths if Path(p).exists()]
            if valid_photos:
                self.photos_to_add.extend(valid_photos)
                logger.info(f"Marked {len(valid_photos)} photos for addition")
                return True
            return False

        except Exception as e:
            logger.exception("Error adding photos")
            return False

    def delete_current_photo(self, photo_path: str) -> bool:
        try:
            if photo_path and Path(photo_path).exists():
                if photo_path in self.photos_to_add:
                    self.photos_to_add.remove(photo_path)
                else:
                    self.photos_to_delete.append(photo_path)

                logger.info(f"Marked photo for deletion: {photo_path}")
                return True
            return False

        except Exception as e:
            logger.exception(f"Error marking photo for deletion: {e}")
            return False

    def _save_new_photos_to_disk(self, person_name: str) -> bool:
        try:
            if not self.photos_to_add:
                return True

            person = person_service.get_person(person_name)
            if not person:
                logger.error(f"Person not found: {person_name}")
                return False

            person.photos_path.mkdir(parents=True, exist_ok=True)

            existing_photos = list(person.photos_path.glob("*"))
            photo_count = len(existing_photos)

            for photo_path in self.photos_to_add:
                try:
                    src = Path(photo_path)
                    if not src.exists():
                        logger.warning(f"Source photo not found: {photo_path}")
                        continue

                    photo_count += 1
                    dst = person.photos_path / f"{photo_count}{src.suffix}"

                    shutil.copy2(str(src), str(dst))
                    logger.info(f"Saved photo: {dst}")

                except Exception as e:
                    logger.exception(f"Error saving photo {photo_path}: {e}")
                    continue

            self.photos_to_add.clear()
            return True

        except Exception as e:
            logger.exception("Error saving new photos")
            return False

    def _delete_marked_photos(self, person_name: str) -> bool:
        try:
            if not self.photos_to_delete:
                return True

            person = person_service.get_person(person_name)
            if not person:
                logger.error(f"Person not found: {person_name}")
                return False

            for photo_path in self.photos_to_delete:
                try:
                    p = Path(photo_path)
                    if p.exists():
                        p.unlink()
                        logger.info(f"Deleted photo: {photo_path}")

                except Exception as e:
                    logger.exception(f"Error deleting photo {photo_path}: {e}")
                    continue

            self.photos_to_delete.clear()
            return True

        except Exception as e:
            logger.exception("Error deleting marked photos")
            return False

    def update_person(self) -> bool:
        if not self.current_person:
            self.show_error(title="Error", message="No person selected")
            return False

        try:
            new_name = self.view.ids.name.text.strip()
            age_text = self.view.ids.age.text.strip()
            nationality = self.view.ids.nationality.text.strip()
            details = self.view.ids.details.text.strip()
            contact_phone = self.view.ids.contact_phone.text.strip()

            gender = (
                Gender.MALE
                if self.view.ids.gender_male.active
                else Gender.FEMALE
            )

            if not new_name:
                self.show_error(title="Validation Error", message="Name cannot be empty")
                return False

            try:
                age = int(age_text) if age_text else 0
                if age < 0:
                    raise ValueError("Age cannot be negative")
            except ValueError as e:
                self.show_error(title="Validation Error", message=f"Invalid age: {str(e)}")
                return False

            if new_name != self.original_name:
                existing_person = person_service.get_person(new_name)
                if existing_person:
                    self.show_error(
                        title="Error",
                        message=f"Person '{new_name}' already exists in database"
                    )
                    return False

            try:
                person_service.update_person(
                    self.original_name,
                    new_name=new_name,
                    age=age,
                    gender=gender,
                    nationality=nationality,
                    details=details,
                    contact_phone=contact_phone
                )
            except Exception as e:
                logger.exception(f"Error updating person: {e}")
                self.show_error(title="Error", message=f"Failed to update person: {str(e)}")
                return False

            if self.photos_to_delete:
                if not self._delete_marked_photos(new_name):
                    self.show_error(
                        title="Warning",
                        message="Person updated but some photos failed to delete"
                    )

            if self.photos_to_add:
                if not self._save_new_photos_to_disk(new_name):
                    self.show_error(
                        title="Warning",
                        message="Person updated but some photos failed to save"
                    )

            person_service.refresh()

            self.show_info(title="Success", message=f"Person '{new_name}' has been updated")
            logger.info(f"Successfully updated person: {new_name}")
            return True

        except Exception as e:
            logger.exception(f"Error updating person: {e}")
            self.show_error(title="Error", message=f"Failed to update person: {str(e)}")
            return False

    def delete_person(self) -> bool:
        if not self.current_person:
            self.show_error(title="Error", message="No person selected")
            return False

        try:
            person_name = self.current_person.name
            success = person_service.delete_person(person_name)

            if success:
                person_service.refresh()
                self.show_info(title="Success", message=f"Person '{person_name}' has been deleted")
                logger.info(f"Deleted person: {person_name}")
                return True
            else:
                self.show_error(title="Error", message=f"Failed to delete person '{person_name}'")
                return False

        except Exception as e:
            logger.exception(f"Error deleting person: {e}")
            self.show_error(title="Error", message=f"Failed to delete person: {str(e)}")
            return False