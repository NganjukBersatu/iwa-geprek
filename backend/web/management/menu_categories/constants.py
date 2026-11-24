from app.core.catalog.menu import CATEGORY_KIND

NOT_FOUND = 404
CONFLICT = 409

# Matches the length of the name column; the list is bounded so one screen can always show every category.
MAX_NAME_LENGTH = 100
MAX_CATEGORIES = 200

__all__ = ["CATEGORY_KIND", "CONFLICT", "MAX_CATEGORIES", "MAX_NAME_LENGTH", "NOT_FOUND"]
