from core import config
from core.logger import AppLogger
from services import person_service
from ui.presenters.base_presenter import BasePresenter

logger = AppLogger().get_logger(__name__)


class PersonsPresenter(BasePresenter):
    def __init__(self, view):
        super().__init__(view)
        self.selected_person = None
        self._initialize_data()

    def _initialize_data(self) -> None:
        try:
            person_service.refresh()

            persons = person_service.get_all_persons()
            if persons:
                self.selected_person = persons[0]

            logger.info("PersonsPresenter initialized")
        except Exception as e:
            logger.exception("Error initializing PersonsPresenter")

    def start(self) -> None:
        try:
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
            if self.selected_person:
                self.view.set_person_info(self.selected_person)

            if hasattr(self.view.ids, 'rv') and not self.view.ids.rv.data:
                logger.info("Updating persons recyclerview")
                if person_service.registry.get_count():
                    self.view.ids.rv_box.select_node(0)

            if hasattr(self.view.ids, 'rv') and hasattr(self.view.ids, 'search_input'):
                if not person_service.registry.get_count():
                    self.empty_recyclerview()
                elif self.view.ids.search_input.text:
                    persons = person_service.search_persons(self.view.ids.search_input.text)
                    if persons:
                        self.refresh_recyclerview(persons)
                    else:
                        self.empty_recyclerview()
                else:
                    persons = person_service.get_all_persons()
                    self.refresh_recyclerview(persons)

        except Exception as e:
            logger.exception("Error updating view")

    def refresh_recyclerview(self, person_list):
        data = [{'text': person.name, 'person': person} for person in person_list]
        self.view.ids.rv.data = data

    def empty_recyclerview(self):
        self.selected_person = None
        self.view.ids.rv.data = [{'text': config.ui.TEXTS["no_elements"]}]
        self.clear_person_info()

    def clear_person_info(self):
        self.view.ids.name.text = ''
        self.view.ids.age.text = ''
        self.view.ids.gender.text = ''
        self.view.ids.nationality.text = ''
        self.view.ids.details.text = ''
        self.view.ids.contact_phone.text = ''
        self.view.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
        self.view.ids.preview_photo_name.text = '(0/0)'

    def search_person(self, text_filter):
        search_person_list = []
        self.view.ids.rv_box.select_node(0)
        for person in person_service.get_all_persons():
            if text_filter.lower() in person.name.lower():
                search_person_list.append(person)
        if len(search_person_list):
            self.refresh_recyclerview(search_person_list)
        else:
            self.empty_recyclerview()
