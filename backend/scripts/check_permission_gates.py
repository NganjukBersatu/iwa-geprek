"""Penjaga gerbang izin: layar, kemampuan, dan rute laporan harus memakai kunci yang ada di katalog dan satu tabel.

Dijalankan dari v2/backend: python scripts/check_permission_gates.py; keluar dengan kode 1 bila ada pelanggaran.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# Hanya memuat modul untuk dibaca; tidak ada koneksi yang dibuka.
os.environ.setdefault("DATABASE_URL", "postgresql://check:check@127.0.0.1:1/check")
os.environ.setdefault("JWT_SECRET_KEY", "check-only-secret-not-used-for-anything-0123456789")

REMOVED_KEYS = ("laporan.lihat",)
# Kunci yang ditulis sebagai teks di rute hanya boleh lewat konstanta berkas gerbangnya.
REPORT_ROUTE_LITERAL = re.compile(r"require_(permission|gate)\(\s*[\"']laporan\.")


def source_problems() -> list[str]:
    found: list[str] = []
    for folder in ("app", "web"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            relative = path.relative_to(ROOT).as_posix()
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.lstrip().startswith("#"):
                    continue
                for key in REMOVED_KEYS:
                    if f'"{key}"' in line or f"'{key}'" in line:
                        found.append(f"{relative}:{number}: kunci lama {key} masih dipakai")
                if relative.startswith("web/management/reports/") and REPORT_ROUTE_LITERAL.search(line):
                    found.append(f"{relative}:{number}: rute laporan menulis kunci sendiri, pakai web/management/reports/gates.py")
    return found


# Rute tablet yang membaca atau menulis data bernilai wajib punya gerbang izin di tiap rutenya.
GATED_MODULES = ("app/operational/stock/routes.py",)
ROUTE_START = re.compile(r"(?m)^@router\.(get|post|patch|put|delete)\(")


def ungated_routes() -> list[str]:
    found: list[str] = []
    for relative in GATED_MODULES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        parts = ROUTE_START.split(text)
        for index in range(2, len(parts), 2):
            block = parts[index]
            name = re.search(r"def (\w+)", block)
            signature = block.split("):", 1)[0]
            if "require_permission(" not in signature and "require_gate(" not in signature:
                found.append(f"{relative}: rute {name.group(1) if name else '?'} tanpa gerbang izin")
    return found


# Salinan beku kunci izin di frontend; tiap kunci harus ada di katalog server, kalau tidak tampilan menjanjikan sesuatu yang server tidak kenal.
FRONTEND_COPIES = (
    ("v2/frontend/app/shared/src/commonMain/kotlin/id/kongstudio/cafe/feature/access/Permission.kt", re.compile(r'\w+\("([a-z_.]+)"\)')),
    ("v2/frontend/web/employee/src/lib/auth/permissions.ts", re.compile(r"\w+:\s*'([a-z_.]+)'")),
)


def frontend_problems() -> list[str]:
    from app.core.permissions.registry import ALL_KEYS

    found: list[str] = []
    repo = ROOT.parent.parent
    for relative, pattern in FRONTEND_COPIES:
        path = repo / relative
        if not path.exists():
            found.append(f"{relative}: berkas salinan izin tidak ditemukan")
            continue
        for key in pattern.findall(path.read_text(encoding="utf-8")):
            if key not in ALL_KEYS:
                found.append(f"{relative}: kunci {key} tidak ada di katalog izin server")
    return found


def registry_problems() -> list[str]:
    import server  # noqa: F401  (memuat semua rute)
    from app.core.auth import AnyOf
    from app.core.permissions.registry import ALL_KEYS
    from web.management.reports import gates
    from web.management.screens import registry

    found: list[str] = []
    # Dua skema bernama sama dari modul berbeda diganti namanya oleh FastAPI dengan awalan modul, dan tipe frontend yang menunjuk nama asli rusak.
    from server import app

    for name in sorted(app.openapi().get("components", {}).get("schemas", {})):
        if "__" in name and not name.startswith("Body_"):
            found.append(f"skema OpenAPI {name} bernama ganda; beri nama unik di salah satu modul")
    for screen in registry.Screen:
        if screen not in registry.GATE_OF:
            found.append(f"layar {screen.value} tidak punya gerbang di GATE_OF")
    for ability in registry.Ability:
        if ability not in registry.ABILITY_GATE:
            found.append(f"kemampuan {ability.value} tidak punya gerbang di ABILITY_GATE")

    def keys_of(gate) -> set[str]:
        if isinstance(gate, str):
            return {gate}
        if isinstance(gate, AnyOf):
            return set(gate.keys)
        return set()

    used: set[str] = set()
    for gate in [*registry.GATE_OF.values(), *registry.ABILITY_GATE.values()]:
        used |= keys_of(gate)
    for key in sorted(used - ALL_KEYS):
        found.append(f"gerbang memakai kunci {key} yang tidak ada di katalog izin")

    report_keys = {value for name, value in vars(gates).items() if name.isupper() and isinstance(value, str) and value.startswith("laporan.")}
    for key in sorted(report_keys - ALL_KEYS):
        found.append(f"gates.py memuat kunci {key} yang tidak ada di katalog izin")
    for key in sorted(k for k in ALL_KEYS if k.startswith("laporan.") and k not in report_keys):
        found.append(f"katalog memuat kunci {key} yang tidak ada di gates.py")
    return found


def main() -> int:
    found = [*source_problems(), *ungated_routes(), *registry_problems(), *frontend_problems()]
    if not found:
        print("Gerbang izin: layar, kemampuan, dan laporan konsisten dengan katalog.")
        return 0
    print("Gerbang izin tidak konsisten:")
    for item in found:
        print(f"  {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
