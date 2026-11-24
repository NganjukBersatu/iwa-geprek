"""Penjaga sumber harga pokok menu: hanya satu pintu yang boleh menulisnya, supaya resep dan harga tetap tidak bisa saling bertabrakan.

Dijalankan dari v2/backend: python scripts/check_cost_sources.py; keluar dengan kode 1 bila ada pelanggaran.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANNED = ("app", "web")

# (pola penulisan, satu-satunya berkas yang boleh memakainya)
RULES = (
    (re.compile(r"\.fixed_cost\s*="), {"app/core/catalog/fixed_cost.py"}),
    (re.compile(r"\bMenuOutletCost\("), {"app/core/catalog/fixed_cost.py"}),
    (re.compile(r"(delete|update|insert)\(\s*(MenuOutletCost|RecipeIngredient)\b"), {"app/core/catalog/fixed_cost.py", "app/core/catalog/recipes.py"}),
    (re.compile(r"\bRecipeIngredient\("), {"app/core/catalog/recipes.py"}),
)


def violations() -> list[str]:
    found: list[str] = []
    for folder in SCANNED:
        for path in sorted((ROOT / folder).rglob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("app/models/"):
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.lstrip().startswith("#"):
                    continue
                for pattern, allowed in RULES:
                    if pattern.search(line) and relative not in allowed:
                        found.append(f"{relative}:{number}: {line.strip()}")
    return found


def main() -> int:
    found = violations()
    if not found:
        print("Sumber harga pokok menu: semua penulisan lewat pintunya.")
        return 0
    print("Penulisan sumber harga pokok menu di luar pintunya (app/core/catalog/fixed_cost.py dan recipes.py):")
    for item in found:
        print(f"  {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
