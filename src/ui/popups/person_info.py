# Copyright (C) 2021 Andrii Sonsiadlo

import os

from kivy.clock import mainthread
from kivy.uix.popup import Popup

from Popup.plot_popup import PlotPopup
from person.person import Person


class PersonInfoPopup(Popup):
	show_popup_person_info = 0

	def __init__(self, person: Person, **kwargs, ):
		super().__init__(**kwargs)
		self.current_person = person
		self.title = self.current_person.name
		self.set_person_info()

	def set_person_info(self):
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
		self.ids.preview_photo.source = './Graphics/Images/default-user-original.png'
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
