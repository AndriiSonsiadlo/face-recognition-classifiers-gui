# Copyright (C) 2021 Andrii Sonsiadlo

import logging
import os
import re
import tkinter as tk
from os import path
from tkinter import filedialog

import cv2
import dlib
from imutils.face_utils import rect_to_bb
from kivy.clock import mainthread
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from Popup.my_popup_warn import MyPopupWarn
from classes.Popup.my_popup_info import MyPopupInfo
from classes.Popup.plot_popup import PlotPopup
from classes.person.person import Person
from core import config
from person.person_list import PersonList
from functions.get_image_dimensions import get_crop_dims


class PopupBox(Popup):
	pop_up_text = ObjectProperty()

	def update_pop_up_text(self, p_message):
		self.pop_up_text.text = p_message


class AddPerson(Screen):
	new_person = Person()
	preview_photo_index = 0

	def __init__(self, **kw):
		super().__init__(**kw)
		# set rules for logging
		logging.basicConfig(level=logging.DEBUG,
		                    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
		                    filename='app.log',
		                    filemode='w')

		# clearing all field in screen for the entering data
		self.clear_inputs()

		# updating list of persons, checking existed files of person in directory
		self.person_list = PersonList()

	# !!!self.person_list.update_person_list()

	def refresh(self):
		logging.debug(u'refresh(): pre-entering in a screen')
		self.person_list = PersonList()

	@mainthread
	def load_photos(self):
		logging.debug(u'load_photos(): button action "Choose photos"')

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
			##### self.new_person.photo_paths.clear()

			# every photo is checking, then path is adding to a list of photos
			for img in photo_paths:
				img_lower = img.lower()
				if (img_lower.endswith('.jpeg') or img_lower.endswith('.jpg') or img_lower.endswith(
						'.png') or img_lower.endswith(
					'.bpm') or img_lower.endswith('.tiff')) and not img_lower.startswith("._"):
					self.new_person.photo_paths.append(img)
			num_loaded = len(self.new_person.photo_paths)
			# if photo have loaded first photo is loading
			if len(photo_paths) > 0:
				self.show_preview_photo(index=self.preview_photo_index)
		return num_loaded

	def delete_photo(self):
		if len(self.new_person.photo_paths):
			self.new_person.photo_paths.pop(self.preview_photo_index)
			if len(self.new_person.photo_paths):
				self.ids.num_files.text = str(len(self.new_person.photo_paths)) + " loaded"

				# set photo preview index to 0
				self.preview_photo_index = 0
				self.show_preview_photo(index=self.preview_photo_index)
			else:
				self.set_default_image()

	def set_default_image(self):
		self.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
		self.ids.preview_photo_name.text = '(0/0)'
		self.ids.num_files.opacity = 0
		self.ids.add_photo_icon.opacity = 0.6

	def previous_photo(self):
		logging.debug(u'previous_photo(): button action "<"')

		# switch previous photo
		if self.preview_photo_index > 0:
			self.preview_photo_index -= 1
			self.show_preview_photo(self.preview_photo_index)

	def next_photo(self):
		logging.debug(u'next_photo(): button action ">"')

		# switch next photo
		if self.preview_photo_index < len(self.new_person.photo_paths) - 1:
			self.preview_photo_index += 1
			self.show_preview_photo(self.preview_photo_index)

	def show_preview_photo(self, index):
		logging.debug(u'show_preview_photo(): showing photo and data of photo')

		# show preview photo in a screen if photo have uploaded
		if len(self.new_person.photo_paths) > 0 and len(self.new_person.photo_paths) > index:
			self.ids.count_face_text.opacity = 0

			image = self.new_person.photo_paths[index]
			if (path.exists(image)):
				self.ids.preview_photo.source = image
			else:
				self.new_person.photo_paths.pop(index)
			photo_name = os.path.basename(image)
			self.ids.preview_photo_name.text = photo_name + ' (' + str(index + 1) + '/' + str(
				len(self.new_person.photo_paths)) + ')'
		else:
			self.set_default_image()

	def add_person(self):
		logging.debug(u'add_person(): init data of person')

		# initialization data of a person
		self.new_person.name = self.ids.create_person_name.text
		self.new_person.age = self.ids.create_person_age.text
		self.new_person.gender = ("Male" if self.ids.gender_male.active == True else "Female")
		self.new_person.nationality = self.ids.create_person_nationality.text
		self.new_person.details = self.ids.create_person_details.text
		self.new_person.contact_phone = self.ids.create_contact_phone.text
		self.new_person.create_data_path()

		logging.debug(u'add_person(): checking current name')

		print(re.search(r'\d(0,0)\w([a-z]){2,20}', self.new_person.name.lower()))

		# checking name already existing person
		if self.person_list.check_name_exists(self.new_person.name):
			self.show_popup_warn(title=f"The person {self.new_person.name} already exist in list")
		# checking incorrect name
		elif (re.search(r'\D([a-z]){2,20}', self.new_person.name.lower())) == None or not self.new_person.name:
			self.show_popup_warn(title="Incorrect person name")
		else:
			logging.debug(u'add_person(): creating isn`t existing directories')
			# creating isn't existing directories
			try:
				if not os.path.isdir(folder_persons_data):
					os.mkdir(folder_persons_data)
				if not os.path.isdir(self.new_person.data_path):
					os.mkdir(self.new_person.data_path)
				if not os.path.isdir(self.new_person.photo_dir):
					os.mkdir(self.new_person.photo_dir)

				logging.debug(u'add_person(): adding person to a list and saving data of him')
				# adding person to a list and saving data of him
				self.person_list.add_person(self.new_person)
				self.new_person.save_photos()
				self.new_person.save_json()

				self.clear_inputs()

				self.show_popup_info(title="Person has been added to a registry")
			except:
				self.show_popup_warn(title="Error")

	def init_new_person(self):
		self.new_person = Person()
		self.new_person.clear()

	def cropping(self):
		if not self.new_person.photo_paths:
			return

		if not path.exists(path_temp):
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
				self.new_person.photo_paths[self.preview_photo_index] = cropped_path
				self.show_preview_photo(self.preview_photo_index)

				print("Cropped: " + f"{crop_dir}/{OutName}")
			cv2.destroyAllWindows()

	def face_detection(self):
		image_path = self.ids.preview_photo.source
		if self.new_person.photo_paths:
			detector = dlib.get_frontal_face_detector()
			image = cv2.imread(image_path)
			rects = detector(image, 1)
			self.ids.count_face_text.text = str(f"Number of faces found: {len(rects)}")
			self.ids.count_face_text.opacity = 1

	def face_detection_backup(self):
		logging.debug(u'face_detection(): scanning face on loaded photo')

		if self.toggle:
			image_path = self.ids.preview_photo.source
			filename = image_path.split("/")[-1]
			temp_dir = f"{path_temp}\\{filename}"

			if self.ids.preview_photo.source != '' and not path.exists(temp_dir):
				detector = dlib.get_frontal_face_detector()
				image = cv2.imread(image_path)
				rects = detector(image, 1)
				for (i, rect) in enumerate(rects):
					# convert dlib's rectangle to a OpenCV-style bounding box
					# [i.e., (x, y, w, h)], then draw the face bounding box
					(x, y, w, h) = rect_to_bb(rect)
					cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

					# show the face number
					cv2.putText(image, "Face #{}".format(i + 1), (x - 10, y - 10),
					            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

				if len(rects) > 0:
					if not os.path.isdir(path_temp):
						os.mkdir(path_temp)

					cv2.imwrite(temp_dir, image)
					self.ids.preview_photo.source = temp_dir
				self.toggle = False
		else:
			self.show_preview_photo(self.preview_photo_index)

	@mainthread
	def clear_inputs(self):
		logging.debug(u'clear_inputs(): clearing all ui-field in a screen')

		self.ids.create_person_name.text = ''
		self.ids.create_person_age.text = ''
		self.ids.gender_male.active = True
		self.ids.create_person_nationality.text = ''
		self.ids.create_person_details.text = ''
		self.ids.create_contact_phone.text = ''

		self.ids.preview_photo.source = str(config.images.DEFAULT_USER_IMAGE)
		self.ids.preview_photo_name.text = '(0/0)'
		self.ids.num_files.opacity = 0
		self.ids.add_photo_icon.opacity = 0.6

		self.ids.count_face_text.opacity = 0

		self.init_new_person()

	def popup_photo(self):
		if (len(self.new_person.photo_paths)):
			try:
				popupWindow = PlotPopup(
					self.ids.preview_photo.source)  # new_person.photo_paths[self.preview_photo_index])
				popupWindow.open()
			except BaseException:
				pass

	def show_popup_warn(self, title):
		popupWindow = MyPopupWarn(text=title)
		# popupWindow.bind(on_dismiss=self.popup_refresh)
		popupWindow.open()

	def show_popup_info(self, title):
		popupWindow = MyPopupInfo(text=title)
		# popupWindow.bind(on_dismiss=self.popup_refresh)
		popupWindow.open()
