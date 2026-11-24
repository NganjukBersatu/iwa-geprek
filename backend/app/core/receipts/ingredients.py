"""Which of the branch's ingredients a receipt line names: it only picks among what exists, never adds one, and only fills the line itself when it is sure."""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Unit
from app.models.ingredient import Ingredient

# Sure enough to fill the line on its own; below it the person picks from the suggestions.
PICK_SCORE = 0.85
# Ahead of the runner-up by this much, so two near-equal names are never decided silently.
PICK_LEAD = 0.1
SUGGEST_SCORE = 0.5
MAX_SUGGESTIONS = 3
# Shorter printed words ("gr", "uk") match too many names to count as an abbreviation.
MIN_ABBREVIATION = 3
PREFIX_SCORE = 0.9
ABBREVIATION_SCORE = 0.8
# The ingredient's own words decide most; the printed words left over only break ties ("Susu" against "Susu UHT").
NAME_WEIGHT = 0.7

# Sizes and counts printed beside a name say nothing about which ingredient it is.
SIZES = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:kg|gr|g|gram|ml|l|lt|ltr|liter|pcs|pc|pack|pak|bks|btl|sachet|x)?\b")
NOT_LETTERS = re.compile(r"[^a-z]+")


@dataclass(frozen=True)
class IngredientRef:
    id: str
    name: str
    unit_id: str | None
    unit_name: str | None


@dataclass(frozen=True)
class IngredientMatch:
    picked: IngredientRef | None
    suggestions: tuple[IngredientRef, ...]


NO_MATCH = IngredientMatch(None, ())


def _words(text: str) -> list[str]:
    return NOT_LETTERS.sub(" ", SIZES.sub(" ", text.lower())).split()


def _is_abbreviation(short: str, word: str) -> bool:
    """"psr" for "pasir": same first letter, then the rest in order."""
    if short[0] != word[0]:
        return False
    rest = iter(word[1:])
    return all(letter in rest for letter in short[1:])


def _word_score(word: str, printed: str) -> float:
    if word == printed:
        return 1.0
    if len(printed) >= MIN_ABBREVIATION:
        if word.startswith(printed):
            return PREFIX_SCORE
        if _is_abbreviation(printed, word):
            return ABBREVIATION_SCORE
    return SequenceMatcher(None, word, printed).ratio()


def _score(name_words: list[str], printed_words: list[str]) -> float:
    covered = sum(max(_word_score(word, printed) for printed in printed_words) for word in name_words) / len(name_words)
    used = sum(max(_word_score(word, printed) for word in name_words) for printed in printed_words) / len(printed_words)
    return NAME_WEIGHT * covered + (1 - NAME_WEIGHT) * used


def _match(printed: str, candidates: list[tuple[IngredientRef, list[str]]]) -> IngredientMatch:
    printed_words = _words(printed)
    if not printed_words:
        return NO_MATCH
    ranked = sorted(
        ((_score(words, printed_words), ref) for ref, words in candidates),
        key=lambda scored: scored[0],
        reverse=True,
    )
    close = [(score, ref) for score, ref in ranked if score >= SUGGEST_SCORE]
    if not close:
        return NO_MATCH
    best_score, best = close[0]
    runner_up = close[1][0] if len(close) > 1 else 0.0
    if best_score >= PICK_SCORE and best_score - runner_up >= PICK_LEAD:
        return IngredientMatch(best, ())
    return IngredientMatch(None, tuple(ref for _, ref in close[:MAX_SUGGESTIONS]))


def match(db: Session, outlet_id: str | None, names: list[str]) -> list[IngredientMatch]:
    """One answer per name, in order; without a branch there is nothing to match against."""
    if outlet_id is None or not names:
        return [NO_MATCH for _ in names]
    rows = db.execute(
        select(Ingredient.id, Ingredient.name, Ingredient.unit_id, Unit.name)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .where(Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True))
    ).all()
    candidates = [(IngredientRef(id_, name, unit_id, unit_name), words) for id_, name, unit_id, unit_name in rows if (words := _words(name))]
    if not candidates:
        return [NO_MATCH for _ in names]
    return [_match(name, candidates) for name in names]
