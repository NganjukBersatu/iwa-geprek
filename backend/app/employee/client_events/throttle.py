"""Pagar laju laporan per karyawan; hitungannya per proses, cukup karena yang dijaga hanya banyaknya baris log."""
from collections import OrderedDict, deque
from threading import Lock

from app.employee.client_events.constants import MAX_REPORTS_PER_WINDOW, MAX_TRACKED_USER, WINDOW_SECONDS

_recent: OrderedDict[str, deque[float]] = OrderedDict()
_lock = Lock()


def retry_after_seconds(user_id: str, now_seconds: float) -> int | None:
    """None bila laporan boleh masuk (dan dicatat); selain itu berapa detik lagi karyawan boleh melapor."""
    with _lock:
        times = _recent.pop(user_id, None) or deque()
        while times and now_seconds - times[0] >= WINDOW_SECONDS:
            times.popleft()
        _recent[user_id] = times
        if len(times) >= MAX_REPORTS_PER_WINDOW:
            return max(1, int(WINDOW_SECONDS - (now_seconds - times[0])) + 1)
        times.append(now_seconds)
        while len(_recent) > MAX_TRACKED_USER:
            _recent.popitem(last=False)
        return None
