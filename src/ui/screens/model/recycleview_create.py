from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from core import config
from ui.popups.warn import WarnPopup


class SelectableRecycleBoxLayout_create(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """Adds selection and focus behaviour to the view."""


class SelectableLabel_create(RecycleDataViewBehavior, Label):
    """Add selection support to the Label."""
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)
        return None

    def apply_selection(self, rv, index, is_selected):
        from services import person_service

        name = rv.data[index]["text"]
        if is_selected:
            person = person_service.get_person(name)
            if name == config.ui.TEXTS["no_persons"]:
                return
            if person:
                from ui.popups.person_info import PersonInfoPopup
                PersonInfoPopup(person=person).open()
            else:
                WarnPopup(title=f"{name} not found in database").open()
            self.parent.select_node(None)
