# Copyright (C) 2021 Andrii Sonsiadlo

from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from Popup.my_popup_person_info import MyPopupPersonInfo
from Popup.my_popup_warn import MyPopupWarn
from _const._customization import no_elements_text
from person.person import Person
from person.person_list import PersonList


class SelectableRecycleBoxLayout_create(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
	""" Adds selection and focus behaviour to the view. """

class SelectableLabel_create(RecycleDataViewBehavior, Label):
	""" Add selection support to the Label """
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)

	def __init__(self, **kwargs):
		super(SelectableLabel_create, self).__init__(**kwargs)

	def refresh_view_attrs(self, rv, index, data):
		""" Catch and handle the view changes """
		self.index = index
		return super(SelectableLabel_create, self).refresh_view_attrs(
			rv, index, data)

	def on_touch_down(self, touch):
		""" Add selection on touch down """
		if super(SelectableLabel_create, self).on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			return self.parent.select_with_touch(self.index, touch)

	def apply_selection(self, rv, index, is_selected):
		name = rv.data[index]["text"]
		if not name == no_elements_text and is_selected:
			person_list = PersonList()
			person = person_list.find_first(name)
			if (person is not None):
				self.show_popup_person_info(person=person)
			else:
				self.show_popup_warm(title=f"{name} not found in database")
		""" Respond to the selection of items in the view. """
		pass

	def show_popup_person_info(self, person: Person):
		popupWindow = MyPopupPersonInfo(person=person)
		popupWindow.open()

	def show_popup_warm(self, title):
		popupWindow = MyPopupWarn(text=title)
		popupWindow.open()
