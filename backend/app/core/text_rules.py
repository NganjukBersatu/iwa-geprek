"""Aturan isi teks yang sama untuk nama orang, nama peran, dan kode shift."""
import unicodedata

NAME_EXTRA_CHARACTERS = " .-"


def _is_letter(character: str) -> bool:
    """Huruf dari bahasa apa pun, termasuk tanda aksen yang berdiri sendiri."""
    return character.isalpha() or unicodedata.category(character).startswith("M")


def is_plain_name(text: str) -> bool:
    """Hanya huruf, angka, spasi, titik, dan tanda hubung."""
    return bool(text) and all(_is_letter(character) or character.isdigit() or character in NAME_EXTRA_CHARACTERS for character in text)


def is_shift_code(text: str) -> bool:
    """Diawali huruf dan seterusnya hanya huruf dan angka."""
    return bool(text) and text[0].isalpha() and all(_is_letter(character) or character.isdigit() for character in text)
