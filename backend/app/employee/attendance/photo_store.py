"""Where an attendance photo is kept."""
from app.core.uploads import UploadedFile
from app.employee.attendance.constants import CLOCK_OUT_PHOTO_SUFFIX, PHOTO_FOLDER


def clock_in_path(record_id: str, photo: UploadedFile) -> str:
    return f"{PHOTO_FOLDER}/{record_id}{photo.extension}"


def clock_out_path(record_id: str, photo: UploadedFile) -> str:
    return f"{PHOTO_FOLDER}/{record_id}{CLOCK_OUT_PHOTO_SUFFIX}{photo.extension}"
