"""Serves a stored file to a player: byte ranges let a video seek and start before it is fully downloaded."""
from fastapi import Response

RANGE_PREFIX = "bytes="
PARTIAL_CONTENT = 206
CACHE_SECONDS = 86400


def file_response(content: bytes, content_type: str, range_header: str | None) -> Response:
    headers = {"Accept-Ranges": "bytes", "Cache-Control": f"private, max-age={CACHE_SECONDS}"}
    size = len(content)
    window = _parse_range(range_header, size)
    if window is None:
        return Response(content=content, media_type=content_type, headers=headers)
    start, end = window
    headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return Response(
        content=content[start:end + 1], status_code=PARTIAL_CONTENT, media_type=content_type, headers=headers
    )


def _parse_range(header: str | None, size: int) -> tuple[int, int] | None:
    """A header that cannot be understood means the whole file, which every player accepts."""
    if not header or not header.startswith(RANGE_PREFIX) or size == 0:
        return None
    first, _, last = header[len(RANGE_PREFIX):].partition("-")
    try:
        if first == "":
            start, end = max(0, size - int(last)), size - 1
        else:
            start, end = int(first), int(last) if last else size - 1
    except ValueError:
        return None
    end = min(end, size - 1)
    return (start, end) if start <= end else None
