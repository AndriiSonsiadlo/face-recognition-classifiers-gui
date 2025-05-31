import random

from pydantic.types import NonNegativeInt

from core import config, Gender
from models.person.person_metadata import PersonMetadata

BASE_DIR = config.paths.PERSON_DATA_DIR
AGE_MIN = 20
AGE_MAX = 56


def normalize_folder_name(name: str) -> str:
    return name.replace("_", " ").strip()


def migrate_person_folders():
    for person_dir in BASE_DIR.iterdir():
        if not person_dir.is_dir():
            continue

        original_name = person_dir.name
        normalized_name = normalize_folder_name(original_name)

        if normalized_name != original_name:
            new_dir = person_dir.parent / normalized_name
            if not new_dir.exists():
                print(f"Renaming: {original_name} → {normalized_name}")
                person_dir.rename(new_dir)
                person_dir = new_dir
            else:
                print(f"Folder already exists: {normalized_name}")
                continue

        old_json = person_dir / "person_data.json"
        if old_json.exists():
            print(f"Deleting {old_json}")
            old_json.unlink()

        age = NonNegativeInt(random.randint(AGE_MIN, AGE_MAX))

        person = PersonMetadata(
            name=normalized_name,
            age=age,
            gender=Gender.MALE,
            nationality="",
            details="",
            contact_phone=""
        )
        person.save()


if __name__ == "__main__":
    migrate_person_folders()
