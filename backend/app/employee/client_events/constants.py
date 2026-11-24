# Batas lapor per karyawan: gerbang izin paling banyak melapor beberapa kali per menit, jadi ini hanya pagar terhadap sesi yang menyalahgunakan.
MAX_REPORTS_PER_WINDOW = 10
WINDOW_SECONDS = 60
# Jumlah karyawan yang dilacak sekaligus; yang paling lama tidak melapor dibuang lebih dulu.
MAX_TRACKED_USER = 5000

MAX_ELAPSED_MILLIS = 120_000
REFERENCE_PATTERN = r"^[A-Z0-9]{6}$"
MAX_AGENT_LENGTH = 160
MAX_HEADER_LENGTH = 32
