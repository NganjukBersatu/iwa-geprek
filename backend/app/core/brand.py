"""Identitas merek klien ini: satu-satunya tempat nama dan warna merek ditulis di backend."""
NAME = "IWAGEPREK"
SLUG = "iwageprek"
# Awalan __Host- membuat peramban hanya menerima cookie ini lewat https, untuk host ini saja, dengan Path=/ dan tanpa Domain.
SESSION_COOKIE = f"__Host-{SLUG}_session"
JWT_ISSUER = f"{SLUG}-backend"
JWT_AUDIENCE = f"{SLUG}-api"
# Warna halaman error mandiri, yang dikirim tanpa berkas gaya web.
PAGE_COLORS = {"ink": "#083878", "muted": "#5D6672", "primary": "#015DF7", "primary_deep": "#083878", "page": "#EEF6FC"}
