"""Shrinks large photos before they are stored, keeping the file format."""

MAX_SIDE_PIXELS = 1280
JPEG_WEBP_QUALITY = 82
JPEG_EXTENSIONS = (".jpg", ".jpeg")
WEBP_EXTENSION = ".webp"

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}
UNSHRUNK_EXTENSIONS = frozenset({".mp4", ".mov", ".webm", ".pdf"})
DEFAULT_MIME_TYPE = "application/octet-stream"


def mime_type(extension: str) -> str:
    return MIME_TYPES.get(extension.lower(), DEFAULT_MIME_TYPE)


def shrink(content: bytes, extension: str) -> bytes:
    """Any failure returns the original, because refusing an upload over its size is worse than keeping it big."""
    if extension.lower() in UNSHRUNK_EXTENSIONS:
        return content
    try:
        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None:
            return content

        height, width = image.shape[:2]
        longest = max(height, width)
        if longest <= MAX_SIDE_PIXELS:
            return content

        scale = MAX_SIDE_PIXELS / longest
        smaller = cv2.resize(
            image, (max(1, int(width * scale)), max(1, int(height * scale))), interpolation=cv2.INTER_AREA
        )
        ext = extension.lower()
        if ext in JPEG_EXTENSIONS:
            ok, buffer = cv2.imencode(ext, smaller, [cv2.IMWRITE_JPEG_QUALITY, JPEG_WEBP_QUALITY])
        elif ext == WEBP_EXTENSION:
            ok, buffer = cv2.imencode(ext, smaller, [cv2.IMWRITE_WEBP_QUALITY, JPEG_WEBP_QUALITY])
        else:
            ok, buffer = cv2.imencode(ext, smaller)
        if not ok:
            return content

        encoded = buffer.tobytes()
        return encoded if len(encoded) < len(content) else content
    except Exception:  # noqa: BLE001
        return content
