# IWAGEPREK

Aturan pemrograman user ada di `~/.claude/rules/` (dimuat otomatis, mulai dari `README.md`). File ini hanya memuat nilai khusus proyek ini. Isinya boleh menambah atau mempertegas aturan global, tidak boleh melonggarkannya.

## Gambaran proyek

- Backend sistem operasional IWAGEPREK (kasir, pesanan, stok dan resep, keuangan, absensi dan jadwal, SOP, tugas outlet). Nama resmi aplikasi: **IWAGEPREK**. Teks yang dilihat pengguna, dokumentasi, dan nama di antarmuka memakai nama ini.
- Judul aplikasi di `app/main.py` sudah "IWAGEPREK". Istilah "cafe"/"kafe" masih ada di kode sebagai nama internal dan kontrak dengan klien: tabel `cafe_settings` dan `cafe_promotions`, rute `/cafe-settings`, id layar dan kunci cache `cafe_settings`, kelas `CafeSettings`/`CafePromotion`, nama logger `cafe`, dan teks "kafe" di pesan serta label izin. Semuanya menunggu keputusan user (mengubah tabel dan rute butuh migrasi dan perubahan di klien); jangan diubah sendiri, dan jangan dipakai untuk nama baru.
- Satu backend melayani dua klien: aplikasi mobile (rute `/v2`) dan web manajemen (`/web/management`). Pintu masuknya `backend/server.py`, yang menggabungkan `app.main` dan `web.management.router`.
- Sistem ini **tidak memakai kamera penghitung pengunjung maupun pengenalan wajah**. Fitur dan kode terkait dihapus; jangan menambahkannya lagi. Foto absensi karyawan dan OCR struk bukan bagian dari itu dan tetap ada.
- Sistem ini **punya pelanggan terdaftar, catatan kunjungan, dan benefit mitra** seperti FOMO v2 (migrasi `b1e3a5c7d879`): tabel `customers`, `visits`, `partners`, `partner_employees`, `partner_employee_free_menus`, `benefit_usages`, serta kolom `orders.customer_id` dan `orders.partner_covered`. Pelanggan lintas cabang (tanpa kolom cabang); kunjungan menunjuk cabang lewat `visits.outlet_id`. Semua kunci asing ke pelanggan, mitra, dan pesanan berupa `RESTRICT`, dan pelanggan, mitra, serta karyawan mitra dinonaktifkan lewat status, tidak dihapus. Id tabel mitra bertipe teks seperti tabel lain. Yang sudah terhubung baru saran pelanggan di kasir (`/v2/operational/customers/suggestions`, izin `pelanggan.lihat`) dan pemakaian benefit yang dilepas saat pesanan dibatalkan; rute kelola dan hapus pelanggan, kunjungan, maupun mitra belum ada. Nama bebas ketik di pesanan (`orders.customer_name`) dan kategori pengunjung yang dipilih kasir tetap ada.
- Sistem ini **tidak punya aplikasi customer, portal kerja sama mitra, maupun fotografer**. Tabel `partner_admins` dan `partner_invoices` tidak dibawa; jangan menambahkan portal mitra atau tagihan mitra tanpa keputusan user.
- **Kata sandi tidak pernah disimpan dalam bentuk terbaca.** Hanya hash bcrypt (`password_hash`). Kolom `password_teks` sudah dikosongkan lewat migrasi dan tidak dipakai kode; jangan dihidupkan lagi.
- Kode web manajemen ada di `web/` (frontend, SvelteKit). Aplikasi tablet operasional dan aplikasi karyawan ada di `app/` di akar repositori (Kotlin Multiplatform + Compose; lihat bagian "Aplikasi tablet dan karyawan"). Aturan 6A/6B dan 8.13 (backend dan frontend sekaligus) berlaku untuk web manajemen.

## Tumpukan teknologi

- Python 3.12 (sesuai `backend/railpack.json`), FastAPI, Uvicorn, Pydantic Settings.
- PostgreSQL lewat SQLAlchemy 2.0 (psycopg 3), migrasi dengan Alembic.
- Redis opsional untuk cache dan siklus event langsung (`REDIS_URL` kosong berarti tanpa cache).
- Penyimpanan berkas: bucket kompatibel S3 lewat boto3. Struk dibaca dengan OpenCV, RapidOCR, dan onnxruntime. Ekspor dengan openpyxl dan fpdf2.
- Deploy di Railway dengan Railpack; susunan proyek ada di `.railway/railway.ts`. Perintah sebelum deploy: `python scripts/pra_deploy.py`. Health check: `/health`.
- Daftar versi pustaka: `backend/requirements.txt`. Pustaka baru hanya atas persetujuan user.
- Web manajemen (`web/`): SvelteKit 2 dengan Svelte 5, Vite, Tailwind CSS 4, Skeleton, ECharts untuk grafik, Tabler webfont untuk ikon, TipTap untuk penyunting teks, Leaflet untuk peta, dan Poppins sebagai satu-satunya huruf teks (`@fontsource/poppins`, bobot 400, 500, 600, 700; token `--font-sans` di `app.css`). Daftar versi: `web/package.json`. Pustaka baru hanya atas persetujuan user.

## Jalur penting (semua di bawah `backend/`)

| Isi | Jalur |
|---|---|
| Pintu masuk gabungan | `server.py` |
| Aplikasi mobile v2 | `app/` (`auth`, `employee`, `operational`, `live`, `router.py`) |
| Logika bersama dan aturan inti | `app/core/` (dikelompokkan per domain: `orders`, `finance`, `catalog`, `permissions`, `receipts`, `ocr`, `storage`, dan lain-lain) |
| Model database | `app/models/` |
| Web manajemen | `web/management/<domain>/` (pola: `routes`, `schemas`, `service`, `repository`, `mappers`, `messages`, `constants`, `domain`) |
| Migrasi | `alembic/versions/`. Rantai v2 dimulai dari empat migrasi dasar `a0b1c2d3e401`–`e404` yang membuat tabel inti (semua `IF NOT EXISTS`, jadi database yang sudah ada tidak berubah), lalu `d2f4a6c8e013` dan seterusnya. Tabel baru tidak boleh ditambahkan ke migrasi dasar; buat migrasi baru di ujung rantai. |
| Konfigurasi | `app/core/settings.py` (satu-satunya pembaca variabel lingkungan) |
| Waktu | `app/core/clock.py` |
| Pintu error dan teks pesan | `app/core/errors.py`, `app/core/error_answers.py`, `app/core/messages.py`, dan `messages.py` per domain |
| Batas waktu query | `app/core/query_budget.py` |
| Hak akses | `app/core/permissions/` |
| Cache | `app/core/cache.py`, `app/core/cache_store.py` |

## Web manajemen (frontend, semua di bawah `web/`)

| Isi | Jalur |
|---|---|
| Token warna dan tema | `src/app.css` (satu-satunya sumber warna) |
| Warna grafik | `src/lib/charts/theme.ts` |
| Teks yang dilihat pengguna | `src/lib/text/` |
| Menu dan nama halaman | `src/lib/nav/` (`pages.ts`, `webNav.ts`) |
| Fitur per domain | `src/lib/features/<domain>/` |
| Komponen bersama | `src/lib/components/` |
| Pemeriksaan sebelum rilis | `npm run check` (jenis, palet warna, dan pintu error) |

## Palet warna merek

Warna merek berasal dari jawaban Copier dan hanya ditulis di lapisan merek (`web/src/styles/brand.css`, `pwa/src/brand.css`, `BrandColors.kt`); token di `app.css` hanya meneruskannya. Hex mentah di luar berkas yang diizinkan `npm run check` ditolak.

| Peran | Kode | Token web |
|---|---|---|
| Warna utama: aksi utama dan menu aktif | `#015DF7` | `brand` (hover dan ditekan turunan OKLCH; lebih gelap `#083878`) |
| Aksen | `#CC0B14` | `brand-accent` (lebih gelap `#830000`, lembut `#FDECEE`, garis `#F7C5C8`) |
| Teks utama | `#083878` | `brand-ink` (lembut `#EEF6FC`, garis `#B9CCE8`) |
| Teks sekunder | `#5D6672` | `brand-muted` |
| Latar aplikasi | `#EEF6FC` | `brand-soft` |
| Latar halaman masuk dan sidebar | `#FDFDFD` | `brand-page` |
| Latar yang ditonjolkan | `#DCEEF8` | `brand-tint` |
| Garis dan pembatas | `#C9D8F0` | `brand-line` |
| Teks di atas warna utama | `#FDFDFD` | `brand-on` |

## Aplikasi tablet dan karyawan (`app/` di akar repositori)

- Satu aplikasi Android (Kotlin Multiplatform + Compose) untuk tablet operasional (kasir, papan stasiun, sesi kas, pengeluaran, cetak) dan aplikasi karyawan (absen, jadwal, tugas, SOP, izin, lembur). Peran di tablet berasal dari jadwal. Modul: `core`, `shared`, `androidApp`.
- Disalin dari proyek Camera (6 November 2026) tanpa riwayat git; identitas sudah IWAGEPREK (applicationId `id.iwageprek.management`, warna sesuai palet web). Camera tetap utuh sebagai sumber sampai aplikasi ini terbukti berjalan.
- Alamat server dibaca dari `app/.env` atau variabel lingkungan `V2_BASE_URL` (contoh di `app/.env.example`); tidak ditulis di kode. Keystore dan `keystore.properties` ada di luar repositori.
- Memakai rute `/v2` backend ini. Semua rute yang dipanggil aplikasi sudah ada di backend (stok bahan dan barang jual kembali, pembagian cetak, riwayat stasiun, pesanan tertinggal, catatan pesanan per cabang, cek versi, penanda SOP dibaca) dan semua saklar di `ServerCapabilities` bernilai `true`; kolom nama pelanggan di kasir menyarankan pelanggan terdaftar (`/v2/operational/customers/suggestions`) dan pesanan menyimpan `customer_id` bila dipilih. Setiap tablet memegang stasiun lewat `device_stations` (diatur di Kelola Perangkat), dan tablet kasir adalah yang memegang stasiun Kasir.
- Nama tabel pada langganan `/v2/live` mengikuti nama tabel database (bahasa Inggris); tambahkan nama baru di daftar `...Tables` pada fitur terkait.

## PWA karyawan iPhone (`pwa/` di akar repositori)

- Aplikasi SvelteKit terpisah (adapter-node, `pwa/package.json` sendiri) untuk karyawan pengguna iPhone dan iPad: masuk, absen datang dan pulang (kamera langsung dan lokasi), jadwal, tugas, SOP, izin, lembur, profil. Pengguna Android memakai APK (`app/`); PWA menolak Android, PC, dan Mac (`src/lib/platform/device.ts`).
- Disalin dari PWA karyawan proyek Camera/Fomo (`v2/frontend/web/employee`, 11 November 2026); identitas dan palet sudah IWAGEPREK. Teks bersumber dari `strings.xml` aplikasi Android (`npm run generate` di `pwa/` membuat `src/lib/text/strings.ts`), jadi kata-katanya satu sumber dengan APK.
- Memakai rute `/v2` backend ini lewat penerus `/api/*` di `pwa/src/hooks.server.ts` (variabel `BACKEND_URL`, contoh di `pwa/.env.example`); sesi memakai cookie HttpOnly dari `POST /v2/auth/session`. Setiap permintaan absen membawa `X-App-Client: pwa` dan `X-App-Version`; versi minimum diatur `MIN_VERSION_PWA`.
- Tipe API dibuat dari skema OpenAPI backend (`npm run api:types` di `pwa/`); setelah rute `/v2` berubah, buat ulang.
- Deploy: layanan Railway terpisah dengan Root Directory `pwa` (`pwa/railpack.json`, health check `/health`, didefinisikan di `.railway/railway.ts`).
- CSP ditegakkan (web manajemen dan PWA): tanpa `unsafe-inline`. Nilai gaya dinamis lewat aksi `dynamicStyle` (`web/src/lib/motion/actions.ts`, `pwa/src/lib/platform/dynamic-style.ts`); atribut `style=` dan arahan `style:` Svelte dilarang. Satu gaya inline milik SvelteKit sendiri (elemen `svelte-announcer`) diizinkan lewat hash yang dihitung otomatis dari paketnya (`scripts/csp-hash.*`); build berhenti bila bentuknya berubah. Tooltip grafik berupa elemen DOM (`axisTooltip`), editor TipTap memakai `injectCSS: false` dengan `editor-base.css`. Kamera di aplikasi Layar Utama iPhone punya riwayat masalah dan wajib diuji di iPhone asli.

## Nilai khusus proyek

- **Zona waktu bisnis:** WIB (UTC+7, tanpa daylight saving). Database menyimpan UTC dengan zona waktu; konversi ke WIB hanya lewat `app/core/clock.py`.
- **Bahasa:** kode, nama file, dan nama folder berbahasa Inggris. Teks yang dilihat pengguna berbahasa Indonesia, profesional.
- **Cabang/outlet:** data dipisah per `outlet_id`. Daftar yang disimpan per cabang (metode bayar, kode shift, jenis pengunjung) dicocokkan lintas cabang lewat `master_id` (`app/core/master_id.py`), bukan lewat teks.
- **Pola lapisan yang sudah dipakai:** route tipis → service → repository, dengan error lewat `DomainError` dan teks di `messages.py`. Kode baru meniru pola ini; struktur lama yang menyimpang dilaporkan, bukan ditiru.
- **Batas query:** mengikuti 500 ms di bagian 4.1; penegaknya `query_budget`.
- **Versi klien:** PWA lama ditolak lewat `MIN_VERSION_PWA`; aplikasi Android tidak diperiksa.

## Daftar istilah baku (keputusan user, 6 November 2026)

Satu istilah untuk satu hal di semua teks yang dilihat pengguna (aturan 6.21.1). Istilah di kolom kanan tidak dipakai lagi.

| Dipakai | Tidak dipakai |
|---|---|
| Keuntungan | Profit |
| Ringkasan (nama tampilan dan tab) | Overview |
| Sesuai / Selisih (pemeriksaan non-tunai) | Balance |
| Jenis kelamin | Gender |
| Jumlah fisik (hasil hitung opname) | Real |
| Nama pengguna | Username |
| Kata sandi | Password, Sandi |
| Non-tunai | Non Tunai |
| Omzet | Omset |

Nama kode, kunci data, dan rute tetap bahasa Inggris dan tidak ikut berubah (contoh: `balance`, `gender`, `username`).

## Nilai UI proyek web manajemen (aturan 6.1 dan 6.39; semua di bawah `web/src/`)

| Fondasi | Satu sumber |
|---|---|
| Token warna dan tema | `app.css` |
| Warna grafik | `lib/charts/theme.ts` |
| Breakpoint | `styles/breakpoints.css` |
| Teks yang dilihat pengguna | `lib/text/` |
| Menu dan nama halaman | `lib/nav/pages.ts`, `lib/nav/webNav.ts` |
| Format uang dan angka | `lib/format/currency.ts` |
| Format tanggal dan rentang | `lib/date/range.ts` |
| Pintu jaringan | `lib/api/http.ts` |
| Pintu error ke pengguna | `lib/api/user-message.ts` dengan kalimat di `lib/text/errors.ts` |
| Toast | `lib/components/feedback/toast.svelte.ts` |
| Data langsung (realtime) | `lib/live/live.ts` |
| Halaman detail satu catatan | `lib/features/record-detail/` (kerangka bersama) |

- **Pustaka ikon:** Tabler webfont (kelas `ti ti-…`). **Pustaka grafik:** ECharts. **Huruf teks:** Poppins.
- **Ukuran huruf tetap** (keputusan user, 6 November 2026): dasar 100% (16 px menurut browser), tanpa `clamp()` yang membesar mengikuti lebar layar. Skala 12/14/16/20/24 px, tinggi kontrol 32/40 px.
- **Daftar dan aksi baris** (keputusan user, 6 November 2026, aturan 6.15.2): baris daftar membuka halaman detailnya lewat URL tetap, dan Ubah, Hapus, serta aksi lain ada di halaman detail, bukan di baris. Halaman detail baru memakai kerangka `lib/features/record-detail/` dan butuh endpoint `GET` per ID di backend. Aksi massal tetap di atas daftar. Pengecualian (keputusan user, 10 November 2026): catatan yang hanya punya satu isian, yaitu Kategori Menu, ditambah, diubah, dan dihapus lewat modal di daftarnya sendiri tanpa halaman detail.
- **Wilayah:** Indonesia, WIB, rupiah. Kewajiban hukum aksesibilitas UE/AS (6.40) tidak berlaku otomatis; target teknis tetap WCAG 2.2 AA. Kewajiban UU 27/2022 PDP dicatat di bagian privasi proyek bila diperlukan.

## Belum ditetapkan (isi bila relevan, jangan menebak)

- Kelas perangkat (6.3); breakpoint yang ada ada di `web/src/styles/breakpoints.css`.
- Alat linter/formatter Python yang dipakai.
- Target RPO/RTO dan kebijakan retensi data.

## Hal yang sudah dikunci aturan global dan sering relevan di sini

- `backend/.env` dan kredensial tidak dibaca, ditampilkan, atau disunting (8.8).
- Migrasi, seed, server, dan docker tidak dijalankan tanpa diminta; tulis kodenya dan berikan perintahnya (8.9). Folder ini bukan repositori git, dan perintah git tetap hanya atas perintah user (8.6).
- File tes, seed, dan script bantu tidak dibuat tanpa persetujuan (8.10). `scripts/seed_payment_methods.py` yang sudah ada tidak dijalankan tanpa perintah.
- Migrasi mengikuti expand → migrate → contract (4.12). Rilis berikutnya tidak menghapus apa yang masih dipakai rilis berjalan.
- **Setiap operasi ubah atau hapus berdasarkan ID wajib memeriksa cabang pemanggil**: akun yang terkunci di satu cabang (`user.locked_outlet_id`) tidak boleh menyentuh baris cabang lain, dan baris itu dijawab "tidak ditemukan", bukan "dilarang". Pola ada di `stock_items._card_in_scope`, `attendance`, dan `leave_requests`.
- `/docs`, `/redoc`, dan `/openapi.json` mati kecuali `ENABLE_API_DOCS=true` (hanya untuk pengembangan). `JWT_SECRET_KEY` wajib minimal 32 karakter; aplikasi, Alembic, dan skrip menolak berjalan bila kurang.
- Percobaan salah dibatasi lewat `app/auth/attempts.py` (login per username, kode pemasangan perangkat untuk seluruh sistem). Penjaga baru yang serupa memakai modul yang sama, bukan tabel baru.
- Model baru di `app/models/` otomatis dibaca `alembic/env.py`; model yang diletakkan di luar paket itu (contoh `web/management/non_cash_checks/model.py`) wajib didaftarkan di `MODELS_OUTSIDE_PACKAGE` pada `env.py`.
- Model ORM di proyek ini tidak menyatakan foreign key, indeks, atau unique; semuanya hidup di migrasi. Perubahan model yang menyangkut kolom atau tabel harus disertai migrasinya.
- **Semua nama tabel, kolom, dan tipe enum di database berbahasa Inggris** (keputusan user, 6 November 2026; migrasi `j5o7g9i1c983_english_names` dan `k6p8h0j2d094_cash_sessions`, yang mengganti nama di database lama maupun baru; tabel sesi kas bernama `cash_sessions`, bukan `shifts`). Nama kolom sama dengan nama atribut modelnya, jadi `mapped_column("nama_lain", ...)` dengan nama eksplisit tidak dipakai lagi. Nilai enum (`menunggu`, `hadir`, ...) tetap karena dibaca klien sebagai data. Nama tabel juga dikirim aliran live ke web dan aplikasi (`app/`); daftar nama tabel di aplikasi sudah diganti ke nama baru, dan nama tabel baru yang dipakai aplikasi harus mengikuti nama di database.
- `app/core/migration_check.py` membaca daftar penggantian nama dari migrasi `j5o7g9i1c983` dan `k6p8h0j2d094`, sehingga pemeriksaan pra-deploy tidak menganggap tabel yang diganti nama sebagai hilang; berkas migrasi itu tidak boleh dihapus atau digabung tanpa memindahkan daftarnya.
- Hanya pekerjaan yang sudah diverifikasi yang ditandai selesai (8.11).
