MIN_TOKEN_LENGTH = 8
MAX_TOKEN_LENGTH = 128
# Room for spaces and dashes typed around the eight characters.
MAX_CODE_LENGTH = 32
QR_LIFETIME_SECONDS = 180
# After a scan the tablet may still collect the employee's token for this long.
USER_TOKEN_WINDOW_SECONDS = 120
QR_TOKEN_BYTES = 18
QR_WAITING = "menunggu"
QR_LINKED = "terhubung"
QR_EXPIRED = "kedaluwarsa"
QR_TABLES = frozenset({"device_links"})
NOT_FOUND = 404
# How a tablet sign-in through a scanned QR is named in the list of sign-ins.
QR_DEVICE_LABEL = "Tablet (pindai QR)"
