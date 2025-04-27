import json
import os

from _const._key_json_person import *


def create_person():
	folder_with_person = os.path.join("C://", "Users", "andri", "Downloads", "FaceID_github", "__person dataset", "lfw")

	for dir in os.listdir(folder_with_person):
		path_person_dir = os.path.join(folder_with_person, dir)
		is_dir_person = os.path.isdir(path_person_dir)

		photos_lst = []
		if is_dir_person:
			os.mkdir(os.path.join(path_person_dir, "photos"))
			for file in os.listdir(path_person_dir):
				if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".jpeg"):
					os.replace(os.path.join(path_person_dir, file), os.path.join(path_person_dir, "photos", file))
					photos_lst.append(os.path.join("person_data2", dir, "photos", file))

			if len(photos_lst):
				save_json(dir, photos_lst, path_person_dir)


def save_json(name, photo_lst, path_person):
	person_data_json = {
		information_k: {
			p_is_wanted_k: "Yes",
			p_name_k: name,
			p_age_k: "N/A",
			p_gender_k: "Male",
			p_nationality_k: "N/A",
			p_details_k: "N/A",
			p_contact_phone_k: "N/A",
			p_photo_paths_k: photo_lst,
			p_count_photo_k: len(photo_lst),

			p_date_k: "N/A",
			p_time_k: "N/A",
		},
	}

	# writing to .json file
	with open(os.path.join(path_person, "person_data.json"), "w") as write_file:
		json.dump(person_data_json, write_file)
		json.dumps(person_data_json, indent=4)
	print(f"[INFO] {name} saved data of person to .json...")


# create_person()

Z = [["1", 2], ["2", 3], ["3", 4], ["4", 5], ["5", 6], ["6", 7], ["7", 8]]

x2 = []
y2 = []
for x, y in Z:
	x2.append(x)
	y2.append(y)

print(x2)

print(y2)
