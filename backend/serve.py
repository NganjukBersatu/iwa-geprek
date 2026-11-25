"""Titik masuk server produksi: satu soket yang menerima IPv4 dan IPv6 sekaligus.

Uvicorn dengan --host :: membuka soket khusus IPv6, sehingga cek kesehatan dan domain publik Railway (IPv4) tidak pernah sampai,
sedangkan jaringan privat Railway (IPv6) butuh :: . Soket dual-stack dibuka di sini lalu diserahkan ke Uvicorn.
"""
import os
import socket

import uvicorn

BACKLOG = 2048


def dual_stack_socket(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::", port))
    sock.listen(BACKLOG)
    return sock


def main() -> None:
    port_text = os.environ.get("PORT", "8000")
    if not port_text.isdigit():
        raise SystemExit(f"PORT harus angka, didapat {port_text!r}")
    config = uvicorn.Config("server:app", proxy_headers=True, forwarded_allow_ips="*")
    uvicorn.Server(config).run(sockets=[dual_stack_socket(int(port_text))])


if __name__ == "__main__":
    main()
