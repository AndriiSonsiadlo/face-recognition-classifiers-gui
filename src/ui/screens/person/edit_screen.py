# Copyright (C) 2021 Andrii Sonsiadlo
import logging
import os
import re
import tkinter as tk
from tkinter import filedialog

import cv2
import dlib
from kivy.clock import mainthread
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from Popup.my_popup_warn import MyPopupWarn
from _const._directory import *
from classes.Popup.my_popup_info import MyPopupInfo
from classes.Popup.plot_popup import PlotPopup
from classes.person.person import Person
from person.person_list import PersonList
from functions.get_image_dimensions import get_crop_dims


class PopupBox(Popup):
	pop_up_text = ObjectProperty()

	def update_pop_up_text(self, p_message):
		self.pop_up_text.text = p_message


class EditPerson(Screen):

	def __init__(self, **kw):
		super().__init__(**kw)
		# set rules for logging
		logging.basicConfig(level=logging.DEBUG,
		                    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
		                    filename='app.log',
		                    filemode='w')

		self.person: Person

		# updating list of persons, checking existed files of person in directory
		self.person_list = PersonList()

	def refresh(self):
		logging.debug(u'refresh(): pre-entering in a screen')

		self.preview_photo_index = 0
		self.person_list = PersonList()
		if not self.person_list.is_empty():
			self.person = self.person_list.get_selected()
			self.set_person_data()

	def set_person_data(self):
		self.old_count_photo = int(len(self.person.photo_paths))

		self.ids.create_person_name.text = self.person.name
		self.ids.create_person_age.text = self.person.age
		if self.person.gender == "Male":
			self.ids.create_person_gender_male.active = True
			self.ids.create_person_gender_female.active = False
		else:
			self.ids.create_person_gender_male.active = False
			self.ids.create_person_gender_female.active = True
		self.ids.create_person_nationality.text = self.person.nationality
		self.ids.create_person_details.text = self.person.details
		self.ids.create_contact_phone.text = self.person.contact_phone

		if len(self.person.photo_paths):
			self.ids.num_files.text = str(len(self.person.photo_paths)) + " loaded"
			self.ids.num_files.opacity = 1
			self.ids.add_photo_icon.opacity = 0
		else:
			self.ids.preview_photo_name.text = '(0/0)'
			self.ids.num_files.opacity = 0
			self.ids.add_photo_icon.opacity = 0.6

		self.show_preview_photo(index=self.preview_photo_index)

	def delete_photo(self):
		if len(self.person.photo_paths):

			self.person.photo_paths.pop(self.preview_photo_index)

			if len(self.person.photo_paths):
				self.ids.num_files.text = str(len(self.person.photo_paths)) + " loaded"

				# set photo preview index to 0
				self.preview_photo_index = 0
				self.show_preview_photo(index=self.preview_photo_index)
			else:
				self.ids.preview_photo.source = default_user_image
				self.ids.preview_photo_name.text = '(0/0)'
				self.ids.num_files.opacity = 0
				self.ids.add_photo_icon.opacity = 0.6

	@mainthread
	def load_photos(self):
		logging.debug(u'load_photos(): button action "Choose photos"')

		# set photo preview index to 0
		self.preview_photo_index = 0
		# count of loaded photos
		num_loaded = self.get_photos()
		if num_loaded > 0:
			self.ids.num_files.text = str(num_loaded) + " loaded"
			self.ids.num_files.opacity = 1
			self.ids.add_photo_icon.opacity = 0

		self.get_root_window().raise_window()  # set focus on window

	def get_photos(self):
		root = tk.Tk()
		root.withdraw()

		# set photo preview index to 0
		self.preview_photo_index = 0

		# setting extensions for searching images in explorer
		photo_paths = filedialog.askopenfilenames(filetypes=[("Image files", ".jpeg .jpg .png .bmp .tiff")])
		num_loaded = 0
		if photo_paths:
			logging.debug(u"get_photos(): Uploading photos from the explorer")

			# clearing list of images for uploading new
			##### self.person.photo_paths.clear()

			# every photo is checking, then path is adding to a list of photos
			for img in photo_paths:
				img_lower = img.lower()
				if (img_lower.endswith(('.jpeg')) or img_lower.endswith(('.jpg')) or img_lower.endswith(
						('.png')) or img_lower.endswith(
					('.bpm')) or img_lower.endswith(('.tiff'))) and not img_lower.startswith("._"):
					self.person.photo_paths.append(img)
			num_loaded = len(self.person.photo_paths)

			# if photo have loaded first photo is loading
			if len(photo_paths) > 0:
				self.show_preview_photo(index=self.preview_photo_index)
		return num_loaded

	def previous_photo(self):
		logging.debug(u'previous_photo(): button action "<"')

		# switch previous photo
		if self.preview_photo_index > 0:
			self.preview_photo_index -= 1
			self.show_preview_photo(self.preview_photo_index)

	def next_photo(self):
		logging.debug(u'next_photo(): button action ">"')

		# switch next photo
		if self.preview_photo_index < len(self.person.photo_paths) - 1:
			self.preview_photo_index += 1
			self.show_preview_photo(self.preview_photo_index)

	def show_preview_photo(self, index):
		self.preview_photo_index = index
		logging.debug(u'show_preview_photo(): showing photo and data of photo')

		# show preview photo in a screen if photo have uploaded
		if len(self.person.photo_paths) > 0 and len(self.person.photo_paths) > index:
			self.ids.count_face_text.opacity = 0

			image = self.person.photo_paths[index]
			self.ids.preview_photo.source = image
			photo_name = os.path.basename(image)
			self.ids.preview_photo_name.text = photo_name + ' (' + str(index + 1) + '/' + str(
				len(self.person.photo_paths)) + ')'
		else:
			self.set_default_image()

	def set_default_image(self):
		self.ids.preview_photo.source = default_user_image
		self.ids.preview_photo_name.text = '(0/0)'
		self.ids.num_files.opacity = 0
		self.ids.add_photo_icon.opacity = 0.6

	def accept(self):
		logging.debug(u'add_person(): init data of person')
		# initialization data of a person
		new_name = self.ids.create_person_name.text
		old_name = self.person.name

		self.person.age = self.ids.create_person_age.text
		self.person.gender = ("Male" if self.ids.create_person_gender_male.active == True else "Female")
		self.person.nationality = self.ids.create_person_nationality.text
		self.person.details = self.ids.create_person_details.text
		self.person.contact_phone = self.ids.create_contact_phone.text

		logging.debug(u'add_person(): checking current name')
		# checking name already existing person
		if (new_name.lower() == old_name.lower()):
			self.person.name = new_name
			self.good_edited(old_name)
		elif self.person_list.check_name_exists(new_name):
			self.show_popup_warm(title=f"The person {new_name} already exist in list")
		elif (re.search(r"(\D\w{2})", self.person.name) == "None") or not new_name:
			self.show_popup_info(title="Incorrect name person")
		else:
			self.person.name = new_name
			self.good_edited(old_name)

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
		self.manager.current = 'wanted'

	def cancel(self):
		self.manager.current = 'wanted'

	def cropping(self):
		if not self.person.photo_paths:
			return

		if not os.path.exists(path_temp):
			os.mkdir(path_temp)

		crop_dir = path_temp
		image_path = self.ids.preview_photo.source
		filename = image_path.split('/')[-1]

		x, y, w, h = get_crop_dims(self.ids.preview_photo.source)

		if not isinstance(x, int):
			x = int(x)
		if not isinstance(y, int):
			y = int(y)
		if not isinstance(w, int):
			w = int(w)
		if not isinstance(h, int):
			h = int(h)

		if image_path != '' and w != 0 and h != 0:
			if not image_path.startswith("._"):  # bulletproofing against thumbnail files
				OutName = filename

				print("fileAddress: " + image_path)
				image = cv2.imread(image_path)
				cropped = image[y:y + h, x:x + w]

				cropped_path = f"{crop_dir}/{OutName}"
				# write the cropped image to disk
				if os.path.exists(cropped_path):
					while True:
						i = 1
						temp_cropped_path = f"{cropped_path}_{i}"
						if os.path.exists(temp_cropped_path):
							i += 1
						else:
							cropped_path = temp_cropped_path
							break

				cv2.imwrite(cropped_path, cropped)
				self.person.photo_paths[self.preview_photo_index] = cropped_path
				self.show_preview_photo(self.preview_photo_index)

				print("Cropped: " + f"{crop_dir}/{OutName}")
			cv2.destroyAllWindows()

	def face_detection(self):
		image_path = self.ids.preview_photo.source
		if self.person.photo_paths:
			detector = dlib.get_frontal_face_detector()
			image = cv2.imread(image_path)
			rects = detector(image, 1)
			self.ids.count_face_text.text = str(f"Number of faces found: {len(rects)}")
			self.ids.count_face_text.opacity = 1

	def popup_photo(self):
		if (len(self.person.photo_paths)):
			popupWindow = PlotPopup(self.person.photo_paths[self.preview_photo_index])
			popupWindow.open()

	def show_popup_warm(self, title):
		popupWindow = MyPopupWarn(text=title)
		popupWindow.open()

	def show_popup_info(self, title):
		popupWindow = MyPopupInfo(text=title)
		# popupWindow.bind(on_dismiss=self.popup_refresh)
		popupWindow.open()
