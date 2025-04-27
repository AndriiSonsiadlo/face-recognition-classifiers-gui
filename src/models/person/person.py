# Copyright (C) 2021 Andrii Sonsiadlo

import json
import os
import re

from PIL import Image

from _const._directory import folder_persons_data, file_person_json, folder_person_photo
from _const._key_json_person import *
from get_time import getTime


class Person:
	def __init__(self,
	             is_wanted: str = "Yes",
	             name: str = "Name",
	             age: str = "Age",
	             gender: str = "Gender",
	             nationality: str = "N/A",
	             details: str = "N/A",
	             contact_phone: str = "N/A",
	             photo_paths=[],
	             date='',
	             time=''
	             ):

		self.is_wanted = is_wanted
		self.name = name
		self.age = age
		self.gender = gender
		self.nationality = nationality
		self.details = details
		self.contact_phone = contact_phone
		self.photo_paths = photo_paths

		self.created_date = date
		self.created_time = time

		self.data_path = folder_persons_data + "//" + name
		self.json_path = ''
		self.photo_dir = ''

		self.selected = False

		self.create_data_path()

	def set_time(self):
		if (self.created_date == ''):
			self.created_date = getTime("day") + '.' + getTime("month") + '.' + getTime("year")
		if (self.created_time == ''):
			self.created_time = getTime("hour") + ':' + getTime("minute") + ':' + getTime("second")

	def create_data_path(self):
		self.data_path = folder_persons_data + "//" + self.name
		self.json_path = self.data_path + "//" + file_person_json
		self.photo_dir = self.data_path + "//" + folder_person_photo

	def get_time_created(self):  # return date and time
		return self.created_time + self.created_date

	# return str(self.created.strftime("%d.%m.%Y, %X"))

	def edit_name(self, name: str):
		self.name = name

	def clear(self):
		self.is_wanted = "Yes"
		self.name = "Name"
		self.age = "Age"
		self.gender = "Gender"
		self.nationality = "N/A"
		self.details = "N/A"
		self.contact_phone = "N/A"
		self.photo_paths = []
		self.date = ''
		self.time = ''

	def save_photos(self):
		num_photo = 1
		for (i, path) in enumerate(self.photo_paths):
			img = Image.open(path)
			path_person_photo = f'{self.photo_dir}/{num_photo}.jpg'
			img.save(path_person_photo)
			self.photo_paths[i] = (path_person_photo)
			num_photo += 1

	def save_json(self):

		person_data_json = {
			information_k: {
				p_is_wanted_k: self.is_wanted,
				p_name_k: self.name,
				p_age_k: self.age,
				p_gender_k: self.gender,
				p_nationality_k: self.nationality,
				p_details_k: self.details,
				p_contact_phone_k: self.contact_phone,
				p_photo_paths_k: self.photo_paths,
				p_count_photo_k: len(self.photo_paths),

				p_date_k: getTime("day") + '.' + getTime("month") + '.' + getTime("year"),
				p_time_k: getTime("hour") + ':' + getTime("minute") + ':' + getTime("second"),
			},
		}

		# writing to .json file
		print("[INFO] saving data of person to .json...")
		with open(self.json_path, "w") as write_file:
			json.dump(person_data_json, write_file)
			json.dumps(person_data_json, indent=4)
		print("[INFO] saved data of person to .json...")

	def edit(self, old_name, old_count_photo):
		self.print_person_data()
		# self.save_photos()
		old_data_path = self.data_path

		self.edition_save_photo(old_count_photo)
		self.create_data_path()
		if old_name != self.name:
			for (i, photo_path) in enumerate(self.photo_paths):
				self.photo_paths[i] = photo_path.replace(old_name, self.name)
			os.rename(old_data_path, self.data_path)

		self.save_json()
		self.delete_useless_photo()

	def edition_save_photo(self, old_count_photo):
		num = old_count_photo + 1

		for (i, path) in enumerate(self.photo_paths):
			if re.search(self.photo_dir, path):
				pass
			else:
				while True:
					path_person_photo = f'{self.photo_dir}/{str(num)}.jpg'
					if os.path.exists(path_person_photo):
						num += 1
					else:
						num += 1
						break
				print(path)
				img = Image.open(path)
				img.save(path_person_photo)
				self.photo_paths[i] = path_person_photo

	def delete_useless_photo(self):
		for file in os.listdir(self.photo_dir):
			for (i, path) in enumerate(self.photo_paths):
				file_ex = path.split('/')[-1]
				if (str(file) == file_ex):
					break
				if i == (len(self.photo_paths) - 1):
					os.remove(os.path.join(self.photo_dir, file))

	def print_person_data(self):
		print(f"Name: {self.name}")
		print(f"Age: {self.age}")
		print(f"Gender: {self.gender}")
		print(f"Nationality: {self.nationality}")
		print(f"Details: {self.details}")
		print(f"Contact phone: {self.contact_phone}")
		print(f"Photo paths: {self.photo_paths}")
		print(f"Created time: {self.created_time}")
		print(f"Created date: {self.created_date}")
		print(f"Data path: {self.data_path}")
