"""Membuat dua berkas logo struk printer dari satu gambar logo, supaya logo klien bisa diganti tanpa menyusun byte dengan tangan.

    python app/scripts/receipt_logo.py app/core/src/commonMain/composeResources/drawable/brand_logo.png

Membutuhkan opencv-python-headless, yang sudah ada di backend/requirements.txt. Setelah logo berganti, naikkan ReceiptLogo.Version di app.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

SIDE_DOTS = 200
SIDE_BYTES = SIDE_DOTS // 8
BAND_ROWS = 24
# Piksel yang lebih gelap dari ambang ini dicetak hitam, sama dengan kasir web.
DARK_BELOW = 160
OUTPUT = Path(__file__).resolve().parents[1] / "core/src/commonMain/composeResources/files/receipt"


def dots_of(source: Path) -> np.ndarray:
    """Gambar apa pun menjadi kotak 200 x 200 titik hitam-putih, diperkecil utuh dan diletakkan di tengah latar putih."""
    image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise SystemExit(f"Gambar tidak bisa dibaca: {source}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        alpha = image[:, :, 3:4].astype(np.float32) / 255
        image = (image[:, :, :3].astype(np.float32) * alpha + 255 * (1 - alpha)).astype(np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    scale = SIDE_DOTS / max(height, width)
    fitted = cv2.resize(gray, (max(1, round(width * scale)), max(1, round(height * scale))), interpolation=cv2.INTER_AREA)
    canvas = np.full((SIDE_DOTS, SIDE_DOTS), 255, np.uint8)
    top = (SIDE_DOTS - fitted.shape[0]) // 2
    left = (SIDE_DOTS - fitted.shape[1]) // 2
    canvas[top : top + fitted.shape[0], left : left + fitted.shape[1]] = fitted
    return canvas < DARK_BELOW


def full_bytes(dots: np.ndarray) -> bytes:
    """Rata tengah, raster GS v 0 per pita 24 baris, lalu baris baru: dikirim utuh di setiap struk."""
    out = bytearray(b"\x1ba\x01")
    for start in range(0, SIDE_DOTS, BAND_ROWS):
        band = dots[start : start + BAND_ROWS]
        out += b"\x1dv0\x00" + bytes([SIDE_BYTES, 0, band.shape[0], 0]) + np.packbits(band, axis=1).tobytes()
    return bytes(out + b"\n")


def stored_bytes(dots: np.ndarray) -> bytes:
    """Perintah FS q yang menyimpan gambar nomor 1 di memori printer; datanya kolom demi kolom."""
    return b"\x1cq\x01" + bytes([SIDE_BYTES, 0, SIDE_BYTES, 0]) + np.packbits(dots.T, axis=1).tobytes()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    dots = dots_of(Path(sys.argv[1]))
    (OUTPUT / "logo-struk-200.bin").write_bytes(full_bytes(dots))
    (OUTPUT / "logo-struk-200-nv.bin").write_bytes(stored_bytes(dots))
    print(f"Logo struk ditulis ke {OUTPUT} ({int(dots.sum())} titik hitam). Naikkan ReceiptLogo.Version di app.")


if __name__ == "__main__":
    main()
