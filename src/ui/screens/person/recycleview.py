# Copyright (C) 2021 Andrii Sonsiadlo

from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from core import config
from ui.screens.person.screen import PersonsScreen


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
	""" Adds selection and focus behaviour to the view. """

class SelectableLabel(RecycleDataViewBehavior, Label):
	""" Add selection support to the Label """
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def refresh_view_attrs(self, rv, index, data):
		""" Catch and handle the view changes """
		self.index = index
		return super().refresh_view_attrs(rv, index, data)

	def on_touch_down(self, touch):
		""" Add selection on touch down """
		if super().on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			return self.parent.select_with_touch(self.index, touch)
		return None

	def apply_selection(self, rv, index, is_selected):
		""" Respond to the selection of items in the view. """
		self.selected = is_selected
		if is_selected and not rv.data[index]["text"] == config.ui.TEXTS["no_elements"]:
			PersonsScreen.screen.set_person_info(rv.data[index]['person'])
		elif index > len(rv.data):
			PersonsScreen.screen.clear_person_info()
		else:
			pass

class PersonRecycleView(RecycleView):
	def get_selected(self):
		if self.layout_manager.selected_nodes:
			return self.data[self.layout_manager.selected_nodes[0]]
		return None
