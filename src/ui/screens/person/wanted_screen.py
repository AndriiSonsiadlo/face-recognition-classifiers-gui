# Copyright (C) 2021 Andrii Sonsiadlo

import os
import re

from kivy.clock import mainthread
from kivy.uix.screenmanager import Screen

from Popup.my_popup_ask import MyPopupAskPerson
from _const._customization import no_elements_text
from classes.Popup.plot_popup import PlotPopup
from person.person import Person
from person.person_list import PersonList


class WantedPerson(Screen):
	preview_photo_index = 0
	screen = None
	start_selected = False

	def __init__(self, **kw):
		super(WantedPerson, self).__init__(**kw)
		self.person_list = PersonList()
		self.current_person = None
		WantedPerson.screen = self

	def refresh(self):  # update screen

		if not self.start_selected:
			self.start_selected = True
			self.ids.rv_box.select_node(0)

		self.person_list = PersonList()

		# self.person_list.update_person_list()
		self.person_list.read_from_file()
		if not self.person_list.is_empty():
			if (self.ids.search_input.text):
				self.search_person(self.ids.search_input.text)
			else:
				self.clear_search()
		else:
			self.empty_recycleview()
			self.current_person = None

	def empty_recycleview(self, text=no_elements_text):
		data = [{'text': text}]
		self.ids.rv.data = data
		self.clear_person_info()

	def refresh_recycleview(self, person_list):
		data = [{'text': person.name, 'person': person} for person in person_list]
		self.ids.rv.data = data

	def search_person(self, text_filter):
		search_person_list = []
		self.ids.rv_box.select_node(0)
		for person in self.person_list.get_list():
			if re.search(str(text_filter).lower(), person.name.lower()):
				search_person_list.append(person)
		if len(search_person_list):
			self.refresh_recycleview(search_person_list)
		else:
			self.empty_recycleview()

	def clear_search(self):
		if not self.person_list.is_empty():
			self.refresh_recycleview(self.person_list.get_list())
		else:
			self.empty_recycleview()

	def set_person_info(self, person: Person):
		self.current_person = person
		self.person_list.set_selected(person.name)
		self.preview_photo_index = 0

		self.ids.person_name.text = self.current_person.name
		if self.current_person.age == "":
			self.ids.person_age.text = "N/A"
		else:
			self.ids.person_age.text = self.current_person.age

		if self.current_person.nationality == "":
			self.ids.nationality.text = "N/A"
		else:
			self.ids.nationality.text = self.current_person.nationality

		if self.current_person.gender == "":
			self.ids.person_gender.text = "N/A"
		else:
			self.ids.person_gender.text = self.current_person.gender

		if self.current_person.details == "":
			self.ids.details.text = "N/A"
		else:
			self.ids.details.text = self.current_person.details

		if self.current_person.contact_phone == "":
			self.ids.contact_phone.text = "N/A"
		else:
			self.ids.contact_phone.text = self.current_person.contact_phone

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
		if len(self.current_person.photo_paths) > 0:
			image = self.current_person.photo_paths[photo_index]
			self.ids.preview_photo.source = image
			photo_name = os.path.basename(image)
			self.ids.preview_photo_name.text = photo_name + ' (' + str(photo_index + 1) + '/' + str(
				len(self.current_person.photo_paths)) + ')'

			if (len(self.current_person.photo_paths)) == 1:
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
		self.ids.preview_photo.source = './Graphics/Images/default-user-original.png'
		self.ids.preview_photo_name.text = '(0/0)'

	def disable_button(self, button):
		button.disabled = True
		button.opacity = .5

	def enable_button(self, button):
		button.disabled = False
		button.opacity = 1

	def previous_photo(self):
		if self.current_person is not None:
			if self.preview_photo_index > 0:
				self.preview_photo_index -= 1
				self.show_preview_photo(self.preview_photo_index)

	def next_photo(self):
		if self.current_person is not None:
			if self.preview_photo_index < len(self.current_person.photo_paths) - 1:
				self.preview_photo_index += 1
				self.show_preview_photo(self.preview_photo_index)

	def popup_photo(self):
		if (self.current_person is not None) and (len(self.current_person.photo_paths)):
			try:
				popup_window = PlotPopup(self.ids.preview_photo.source)
				popup_window.open()
			except BaseException:
				popup_window = PlotPopup(self.current_person.photo_paths[self.preview_photo_index])
				popup_window.open()

	def delete_person(self):
		selected = self.person_list.get_selected()
		if selected is not None:
			popup_window = MyPopupAskPerson()
			del self.current_person
			popup_window.bind(on_dismiss=self.popup_refresh)
			popup_window.open()
		else:
			print("No selected element")

	def open_screen_add(self):
		self.manager.transition.direction = "left"
		self.manager.current = "add_person"

	def open_screen_edit(self):
		self.manager.transition.direction = "left"
		self.manager.current = "edit_person"

	def edit_person(self):
		if not self.person_list.is_empty():
			selected = self.person_list.get_selected()
			if selected is not None:  # show last model if none has been selected
				self.open_screen_edit()
			else:
				print("No selected element")
		else:
			print("No selected element")

	def popup_refresh(self, instance):  # update screen after pressing delete
		self.refresh()
