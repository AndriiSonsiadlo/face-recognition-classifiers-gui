import os

from core import Gender
from models.person.person_metadata import PersonMetadata


def create_metadata_for_persons():
    lfw_dataset = os.path.join("../lfw")

    for name in os.listdir(lfw_dataset):
        path_person_dir = os.path.join(lfw_dataset, name)
        is_dir_person = os.path.isdir(path_person_dir)

        if is_dir_person:
            PersonMetadata(name=name, gender=Gender.MALE, age=0)


if __name__ == '__main__':
    create_metadata_for_persons()
