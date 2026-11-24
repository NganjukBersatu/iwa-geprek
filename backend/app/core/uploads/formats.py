"""Tells what an upload really is from its content, and turns it into a format the rest of the system keeps."""
from io import BytesIO

from app.core.uploads.file import KIND_DOCUMENT, KIND_PHOTO, KIND_VIDEO, UploadedFile

SIGNATURE_SCAN_BYTES = 1024
MP4_MARK = b"ftyp"
MP4_MARK_OFFSET = 4
MOV_EXTENSION = ".mov"
MP4_EXTENSION = ".mp4"
WEBM_EXTENSION = ".webm"
WEBM_MARK = bytes.fromhex("1A45DFA3")
PDF_MARK = b"%PDF-"
PDF_EXTENSION = ".pdf"
KEPT_PHOTO_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
CONVERTED_EXTENSION = ".jpg"
CONVERTED_QUALITY = 90
PNG_EXTENSION = ".png"
# PNG buram di atas ukuran ini hampir pasti foto; disimpan sebagai JPEG supaya tidak membebani tablet. PNG kecil (kode QR, grafik) tetap tanpa kompresi rugi.
OPAQUE_PNG_PHOTO_BYTES = 512 * 1024
OPAQUE_ALPHA = 255


def identify(extension: str, content: bytes) -> UploadedFile | None:
    """Judges by content, not by name: a HEIC photo called .jpg is still a photo, and a photo in any format is converted."""
    if not content:
        return None
    head = content[:SIGNATURE_SCAN_BYTES]
    if PDF_MARK in head:
        return UploadedFile(KIND_DOCUMENT, PDF_EXTENSION, content)
    if head.startswith(WEBM_MARK):
        return UploadedFile(KIND_VIDEO, WEBM_EXTENSION, content)
    if head[MP4_MARK_OFFSET : MP4_MARK_OFFSET + len(MP4_MARK)] == MP4_MARK and extension in {MOV_EXTENSION, MP4_EXTENSION}:
        return UploadedFile(KIND_VIDEO, extension, content)
    return _photo(extension, content)


def _photo(extension: str, content: bytes) -> UploadedFile | None:
    if extension == PNG_EXTENSION and len(content) > OPAQUE_PNG_PHOTO_BYTES:
        photo = _opaque_png_as_jpeg(content)
        if photo is not None:
            return UploadedFile(KIND_PHOTO, CONVERTED_EXTENSION, photo)
    if extension in KEPT_PHOTO_EXTENSIONS and _decodes(content):
        return UploadedFile(KIND_PHOTO, extension, content)
    converted = _to_jpeg(content)
    return UploadedFile(KIND_PHOTO, CONVERTED_EXTENSION, converted) if converted is not None else None


def _opaque_png_as_jpeg(content: bytes) -> bytes | None:
    """JPEG dari PNG yang tidak memakai transparansi; None bila PNG-nya transparan atau tidak terbaca, sehingga tetap disimpan apa adanya."""
    import cv2
    import numpy as np

    image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim != 3:
        return None
    if image.shape[2] == 4:
        if (image[:, :, 3] < OPAQUE_ALPHA).any():
            return None
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    ok, buffer = cv2.imencode(CONVERTED_EXTENSION, image, [cv2.IMWRITE_JPEG_QUALITY, CONVERTED_QUALITY])
    return buffer.tobytes() if ok else None


def _decodes(content: bytes) -> bool:
    import cv2
    import numpy as np

    return cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR) is not None


def _to_jpeg(content: bytes) -> bytes | None:
    """HEIC from an iPhone, GIF, BMP, TIFF and the like, upright and as an ordinary JPEG."""
    try:
        from PIL import Image, ImageOps
        from pillow_heif import register_heif_opener

        register_heif_opener()
        with Image.open(BytesIO(content)) as opened:
            upright = ImageOps.exif_transpose(opened).convert("RGB")
        out = BytesIO()
        upright.save(out, format="JPEG", quality=CONVERTED_QUALITY)
        return out.getvalue()
    except Exception:  # noqa: BLE001
        return None
