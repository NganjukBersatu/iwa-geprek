import re

from app.core.storage import folders

PHOTO_FOLDER = folders.PROFILE_PHOTO

MAX_NAME_LENGTH = 255
MAX_PHONE_LENGTH = 30
MAX_ADDRESS_LENGTH = 500
MAX_EMAIL_LENGTH = 255
MAX_RELATION_LENGTH = 50

PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{6,30}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
OLDEST_BIRTH_YEAR = 1900
GENDERS = ("L", "P")
