# IWAGEPREK

Backend sistem operasional IWAGEPREK: kasir dan pesanan, stok dan resep, keuangan, absensi dan jadwal, SOP, serta tugas outlet. Satu layanan FastAPI melayani aplikasi mobile (`/v2`) dan web manajemen (`/web/management`).

Aturan kerja proyek ada di [`CLAUDE.md`](CLAUDE.md).

## Tumpukan
Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis (opsional), penyimpanan berkas kompatibel S3 (opsional). Deploy di Railway.

## Menjalankan di komputer
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env        # lalu isi DATABASE_URL dan JWT_SECRET_KEY (minimal 32 karakter)
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\create_owner.py --tulis    # membuat cabang pertama dan akun pemilik
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

Dokumentasi API mati secara bawaan. Untuk pengembangan, set `ENABLE_API_DOCS=true` di `.env`, lalu buka `/docs`.

## Struktur
| Jalur | Isi |
|---|---|
| `backend/server.py` | Pintu masuk gabungan aplikasi mobile dan web manajemen |
| `backend/app/` | Aplikasi mobile (`auth`, `employee`, `operational`, `live`) dan logika bersama di `core/` |
| `backend/web/management/` | Web manajemen, satu folder per domain |
| `backend/alembic/versions/` | Migrasi database; rantai dimulai dari empat migrasi dasar `a0b1c2d3e401`–`e404` |
| `backend/scripts/` | `pra_deploy.py` (penjaga deploy) dan `create_owner.py` |

## Deploy
Susunan proyek Railway (backend, web admin, PWA, Postgres, Redis, dan bucket yang sudah tersambung) ada di `.railway/railway.ts`; tiap layanan dibangun Railpack menurut `railpack.json` di foldernya.

1. Pasang Railway CLI versi 5.42.1 atau lebih baru, lalu `railway login` dan `railway link` ke proyek klien ini.
2. `npm install railway` di akar repositori, supaya `.railway/railway.ts` bisa dibaca CLI.
3. `railway config plan` untuk melihat perubahan, lalu `railway config apply` untuk menerapkannya.
4. Isi `JWT_SECRET_KEY` layanan backend di Railway (minimal 32 karakter), dan buat domain publik untuk backend, web, dan pwa.

Railway menjalankan `python scripts/pra_deploy.py` sebelum setiap deploy. Skrip itu menjalankan migrasi dalam satu transaksi, membandingkan jumlah baris dan jumlah uang sebelum dan sesudah, lalu membatalkan semuanya bila ada yang berbeda. Cek kesehatan di `/health`.

Sebelum deploy yang menjalankan migrasi penghapusan data, buat backup database.

## Versi dan catatan rilis
Versi dan ringkasan "Yang baru" milik klien ini; `copier update` tidak menimpanya.

| Bagian | Versi | Ringkasan |
|---|---|---|
| APK | `app/version.properties` (naikkan `versionName` dan `versionCode`) | `strings_release.xml` dan `ReleaseNotes.kt` |
| PWA karyawan | `pwa/version.json` | `strings_release.xml` dan `pwa/src/lib/features/release/release-notes.ts` |
| Web admin | `web/version.json` | `web/src/lib/text/admin-release.ts` dan `web/src/lib/features/release/release-notes.ts` |

Logo, ikon, splash, foto layar masuk, dan logo struk juga milik klien; daftar lengkapnya di `_skip_if_exists` template.

Setelah mengubah versi APK atau PWA, jalankan `npm run generate` di `web/` supaya halaman Unduhan ikut berubah.

## Data demo untuk presentasi
Data demo tinggal di skema `demo` pada database yang sama dan terpisah penuh dari data asli. Isinya (cabang, menu beserta foto, bahan, resep, pengeluaran, jam sesi kas) diambil dari `backend/scripts/demo_catalog.json` milik klien, lalu dilengkapi penjualan, stok, absensi, jadwal, dan tugas contoh.

1. Data asli harus sudah di migrasi terbaru (`python scripts/pra_deploy.py`).
2. `python scripts/demo_data.py isi` membuat skema demo sekali dan menampilkan kata sandi akun `demo` satu kali.
3. Jalankan backend dengan `DEMO_MODE=true`: proses itu hanya membaca dan menulis skema demo, tidak memakai Redis atau bucket, dan menolak jalan bila skema demo belum ada atau tertinggal migrasi. Perangkat kasir dipasangkan lagi dari web admin demo.
4. Setelah presentasi, matikan `DEMO_MODE` dan jalankan `python scripts/demo_data.py hapus` untuk menghapus seluruh data demo. Setelah migrasi baru, hapus lalu isi lagi.

## Keamanan
- Jangan pernah menyimpan `.env` atau kredensial di repositori; hanya `backend/.env.example` yang boleh.
- Kata sandi hanya disimpan sebagai hash bcrypt.
- Login dibatasi: terlalu banyak kata sandi salah mengunci username untuk sementara.
