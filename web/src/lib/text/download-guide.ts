import { brand } from '$lib/text/brand';
/** One step of a guide; `soon` marks a part of the app that is still being built. */
export type GuideStep = { icon: string; title: string; body: string; soon: boolean };

/** One topic of a guide, shown as its own tab; `who` names the people it is for. */
export type GuideTopic = { key: string; icon: string; title: string; who: string; steps: GuideStep[] };

export type Trouble = { icon: string; title: string; body: string };

/** A whole guide: its topics in the order a newcomer needs them, then help for the usual mistakes. */
export type Guide = { title: string; intro: string; topics: GuideTopic[]; troubles: Trouble[] };

const step = (icon: string, title: string, body: string, soon = false): GuideStep => ({ icon, title, body, soon });

export const TABLET_GUIDE: Guide = {
	title: 'Tablet operasional',
	intro: 'Admin menyiapkan tablet sekali; kasir, stasiun, dan pengelola mengikuti langkah sesuai tugasnya. Menu yang tampil di tablet mengikuti izin peran masing-masing.',
	topics: [
		{
			key: 'setup',
			icon: 'settings',
			title: 'Penyiapan',
			who: 'Admin, sekali per tablet',
			steps: [
				step('key', 'Tambah perangkat', 'Di web, buka Pengaturan, Cabang, pilih cabangnya, buka tab Perangkat, lalu Tambah perangkat. Centang stasiun yang dipegang tablet itu: Kasir, Bar, Dapur, atau Waiters; namanya terisi otomatis. Hanya tablet dengan stasiun Kasir yang bisa membuka sesi dan bertransaksi.'),
				step('building-store', 'Stasiun tanpa tablet', 'Stasiun yang hanya punya printer, tanpa tablet, dicentang di tablet Kasir pada bagian Stasiun tanpa tablet yang dicetak dari sini. Struk menunya dikirim tablet Kasir ke printer di stasiun itu.'),
				step('qrcode', 'Pasangkan tablet', 'Ketuk Buat kode, lalu di tablet pada layar masuk ketuk Menu perangkat, Daftarkan perangkat operasional, dan pindai kode QR-nya. Kode juga bisa diketik bila kamera tidak bisa dipakai.'),
				step('printer', 'Pasang printer di tablet', 'Di tablet, buka Printer. Tablet hanya meminta printer yang dibutuhkan stasiunnya. Nyalakan Bluetooth, pilih printernya, lalu jawab apakah kertas uji tercetak benar.'),
				step('list-check', 'Periksa kesiapan', 'Di web, tab Ringkasan cabang menampilkan Kesiapan cabang, dan tab Stasiun dan Printer menampilkan tablet dan printer setiap stasiun beserta pratinjau rute menu.')
			]
		},
		{
			key: 'signin',
			icon: 'login',
			title: 'Masuk dan keluar',
			who: 'Semua karyawan',
			steps: [
				step('qrcode', 'Masuk dengan QR', 'Di tablet, ketuk Tampilkan QR. Di HP, buka Absen, lalu Pindai QR pada bagian Perangkat operasional dan arahkan kamera ke QR di tablet. QR ditutup sendiri bila lama tidak dipakai; ketuk Tampilkan QR lagi.'),
				step('switch-horizontal', 'Ganti karyawan', 'Karyawan yang sedang masuk ketuk Keluar dulu, lalu karyawan berikutnya masuk dengan QR. Setiap pesanan dan sesi tercatat atas nama yang sedang masuk.'),
				step('logout', 'Keluar', 'Buka menu, lalu ketuk Keluar. Pesanan yang belum terkirim dikirim dulu; tunggu sampai lembar Mengirim pesanan selesai.'),
				step('cash-banknote', 'Keluar saat sesi kasir berjalan', 'Tombolnya berubah menjadi Tutup sesi dan keluar. Hitung uang di laci, isi Uang aktual di laci sekarang, lalu tutup. Tablet baru bisa keluar setelah sesi ditutup.'),
				step('wifi-off', 'Keluar saat internet putus', 'Bila muncul Status sesi belum terbaca, sambungkan internet dulu supaya sesi dan pesanan tidak tertinggal.')
			]
		},
		{
			key: 'cashier',
			icon: 'shopping-cart',
			title: 'Kasir dan sesi',
			who: 'Kasir',
			steps: [
				step('cash', 'Buka sesi', 'Ketuk Buka sesi dan isi Uang di laci saat mulai. Satu kasir hanya punya satu sesi berjalan.'),
				step('tools-kitchen-2', 'Pilih menu', 'Cari atau pilih menu. Isi varian yang Wajib dipilih, ekstra, dan Catatan untuk menu ini, lalu Tambah ke pesanan. Menu bertanda Habis, Bahan habis, atau Belum ada resep tidak bisa dipesan.'),
				step('armchair', 'Isi data pesanan', 'Pilih Free Table atau Take Away. Isi nama atau nomor HP pelanggan, nomor meja, dan Catatan untuk seluruh pesanan bila perlu. Kategori pengunjung boleh dikosongkan.'),
				step('credit-card', 'Bayar', 'Ketuk Bayar, pilih metode dan promo bila ada. Untuk tunai isi Uang diterima atau ketuk Uang pas, lalu serahkan kembaliannya. Untuk non-tunai, Tunjukkan ke Pelanggan menampilkan QR dan totalnya. Ketuk Simpan transaksi.'),
				step('coins', 'Kelebihan pembayaran non-tunai', 'Bila nominal masuk ke rekening lebih besar dari total, jangan beri kembalian tunai. Kelebihannya tercatat otomatis di Kelebihan Pembayaran.'),
				step('trash', 'Kosongkan pesanan', 'Kosongkan pesanan menghapus semua item, data pelanggan, catatan, dan promo pada pesanan yang belum dibayar, setelah dikonfirmasi.'),
				step('list-details', 'Daftar pesanan', 'Buka Papan Stasiun, tab Kasir. Cari pesanan sesi ini, ketuk untuk rinciannya, lalu cetak ulang struk (bertanda Cetak Ulang) atau Ajukan Pembatalan. Pembatalan berlaku setelah disetujui admin di web.'),
				step('alert-triangle', 'Pesanan tertinggal', 'Saat sesi baru dibuka, pesanan dari sesi lain yang belum selesai di stasiun muncul di modal dan di atas daftar pesanan dengan lencana merah. Pastikan stasiun menyelesaikannya.'),
				step('clock', 'Sesi Kasir Saya', 'Lihat sesi yang berjalan, riwayat sesi, dan pesanannya. Tutup sesi dari sini atau lewat Keluar.'),
				step('circle-check', 'Tutup sesi', 'Isi uang aktual di laci; bila cabang memakai tiga bagian uang, isi Modal, Uang belanja, dan Omzet tunai terpisah. Selisih tercatat otomatis. Pesanan yang belum selesai tetap di antrean stasiun.')
			]
		},
		{
			key: 'stations',
			icon: 'layout-kanban',
			title: 'Papan Stasiun',
			who: 'Bar, Dapur, dan Waiters',
			steps: [
				step('layout-kanban', 'Buka Papan Stasiun', 'Menu baru masuk otomatis tanpa memuat ulang. Tablet dengan beberapa stasiun menampilkan tab; ketuk atau geser untuk berpindah, dan angka di tab menunjukkan menu yang menunggu.'),
				step('list-numbers', 'Baca antrean', 'Yang paling lama menunggu ada di atas. Menu berlencana merah Tertinggal berasal dari sesi kasir yang sudah ditutup dan selalu paling atas, jadi kerjakan lebih dulu.'),
				step('player-play', 'Mulai', 'Ketuk satu kelompok untuk membuka halaman kerjanya. Bar dan Dapur melihat takaran resep sesuai jumlah porsi. Ketuk tujuan untuk memilih sebagian, lalu Mulai Proses.'),
				step('check', 'Selesai', 'Ketuk Selesai. Bila printer stasiun dipasang di tablet ini, struk pesanan tercetak satu per menu untuk diletakkan di bawah piring atau gelasnya, lalu menu pindah ke Waiters.'),
				step('walk', 'Antar', 'Waiters mengetuk meja tujuan, Antar Sekarang saat membawa, lalu Sudah Diantar setelah sampai.'),
				step('arrow-back-up', 'Salah tekan', 'Buka kelompok yang salah lalu ketuk Kembalikan ke Antrean. Menu yang sudah dibawa pengantar tidak bisa dikembalikan dari stasiun pembuat.'),
				step('alert-octagon', 'Hentikan', 'Menu yang dibatalkan atau dihapus lewat koreksi muncul merah di bagian Hentikan. Jangan dibuat atau diantar, lalu ketuk Mengerti.'),
				step('history', 'Riwayat dan cetak ulang', 'Ketuk Riwayat untuk melihat menu yang sudah selesai beserta keadaan terakhirnya. Buka satu menu untuk melihat perjalanan pesanannya dan ketuk Cetak Ulang Struk Pesanan.'),
				step('volume', 'Bunyi menu baru', 'Menu baru berbunyi. Saklar Bunyi menu baru di atas antrean mematikan atau menyalakan bunyi khusus stasiun itu di tablet ini.')
			]
		},
		{
			key: 'inventory',
			icon: 'package',
			title: 'Inventori',
			who: 'Sesuai izin stok',
			steps: [
				step('list', 'Daftar Bahan', 'Melihat stok setiap bahan di cabang ini. Bahan bertanda Stok menipis perlu segera dibeli.'),
				step('truck-delivery', 'Barang Masuk', 'Ketuk +, pilih bahan, isi jumlah sesuai satuannya, lalu Simpan. Yang dicatat hanya jumlah; harga beli dicatat di Pengeluaran.'),
				step('flask', 'Rusak dan RnD', 'Pilih tab Rusak atau RnD, ketuk +, pilih bahan, dan isi jumlah. Untuk Rusak pilih sebabnya (sebab Lainnya wajib dengan catatan); untuk RnD catatan wajib diisi. Simpan, dan stok berkurang sebesar jumlah itu.'),
				step('clipboard-check', 'Stok Opname', 'Hanya untuk peran dengan izin Tutup periode. Hitung fisik bahan dan isi Jumlah real; bahan yang dikosongkan dianggap tidak dihitung. Draf tersimpan otomatis dan bisa dilanjutkan di web atau tablet lain. Tutup periode menyamakan stok, lalu seluruh stok bahan cabang ini kembali 0 untuk periode baru, termasuk yang tidak dihitung. Menu yang memakai bahan itu tidak bisa dipesan sampai admin mengisi Stok awal di web. Satu periode hanya bisa ditutup sekali; perbaikan dan pembatalan dilakukan admin dari halaman detail periode di web.'),
				step('tag', 'Stok Barang Jual-Ulang', 'Daftar menampilkan stok dengan penanda Habis atau Menipis; tab Masuk dan Penyesuaian memuat riwayatnya. Ketuk barang untuk mencatat Barang masuk, Penyesuaian tambah, atau Penyesuaian kurang; penyesuaian wajib beralasan minimal 3 karakter. Untuk menghitung, ketuk Mulai opname, isi Jumlah fisik, lalu Simpan opname. Opname jual-ulang tidak berperiode dan tidak mengembalikan stok ke 0; selisihnya dicatat sebagai penyesuaian.')
			]
		},
		{
			key: 'products',
			icon: 'coffee',
			title: 'Produk',
			who: 'Sesuai izin produk',
			steps: [
				step('coffee', 'Kelola Menu', 'Cari menu untuk mengubah nama, kategori, deskripsi, ketersediaan, dan foto. Menandai tidak tersedia membuat menu tidak bisa dipesan di kasir semua cabang sampai ditandai tersedia lagi. Harga dan harga pokok tetap hanya diatur dari web admin.'),
				step('adjustments', 'Varian dan Ekstra', 'Pilih tab Varian atau Ekstra, lalu Tambah. Isi pilihan dan harganya, tandai Wajib dipilih bila perlu, dan pilih menu yang memakainya.'),
				step('tools-kitchen', 'Master Resep', 'Pilih menu, lalu tambahkan bahan beserta Takaran per porsi. HPP dan margin terhitung otomatis. Menu tanpa resep belum bisa dijual, kecuali memakai harga pokok tetap dari web.'),
				step('discount', 'Promosi', 'Ketuk Tambah promosi. Pilih Diskon kasir atau Info kafe, berlaku untuk Semua item, Produk tertentu, atau Total belanja, potongan Persen atau Nominal, lalu cara aktif Otomatis atau Dipilih kasir.'),
				step('notes', 'Catatan Pesanan', 'Daftar catatan siap pilih di kasir, milik cabang ini saja. Ketuk + untuk menambah; ketuk satu catatan untuk mengganti nama atau menghapusnya. Catatan yang sudah dipakai pesanan hanya bisa diganti nama. Catatan umum berlaku di semua cabang dan hanya diatur dari web. Kasir tetap bisa menambah catatan langsung dari kasir.'),
				step('category', 'Kategori Pengunjung', 'Pilihan kategori dan gender pengunjung yang ditanyakan di kasir.')
			]
		},
		{
			key: 'finance',
			icon: 'wallet',
			title: 'Keuangan',
			who: 'Sesuai izin keuangan',
			steps: [
				step('camera', 'Catat pengeluaran', 'Buka Pengeluaran, ketuk + di kanan judul. Foto nota untuk mengisi baris otomatis, periksa nama dan harga, pilih sumber dana Omzet tunai (uang laci) atau Dana lain, lalu Simpan. Pengeluaran menempel ke sesi kasir Anda yang sedang berjalan.'),
				step('pencil', 'Ubah atau hapus pengeluaran', 'Ketuk pengeluaran untuk rinciannya, lalu Ubah atau Hapus; foto nota juga bisa diganti. Kasir hanya bisa mengubah miliknya sendiri selama sesinya masih berjalan.'),
				step('cash-banknote', 'Kelebihan Pembayaran', 'Daftar pembayaran non-tunai yang lebih besar dari total pesanan. Uangnya ada di rekening, bukan di laci.')
			]
		},
		{
			key: 'device',
			icon: 'device-tablet',
			title: 'Perangkat',
			who: 'Semua karyawan',
			steps: [
				step('wifi-off', 'Mode Offline', 'Melihat pesanan yang Menunggu dikirim. Kirim sekarang mengirim ulang saat internet kembali. Pesanan Ditolak server bisa dilihat, dikirim ulang, atau dihapus.'),
				step('info-circle', 'Info Aplikasi', 'Melihat versi aplikasi dan daftar yang baru di versi itu.'),
				step('download', 'Pembaruan wajib', 'Bila muncul Pembaruan wajib, ketuk Buka halaman unduhan, unduh APK terbaru, lalu pasang. Kasir yang sesinya berjalan boleh melanjutkan sampai sesi ditutup.'),
				step('plug-connected-x', 'Lepas perangkat', 'Hanya admin: buka Menu perangkat, Lepas perangkat, lalu masukkan kode perangkat yang sama.')
			]
		}
	],
	troubles: [
		{ icon: 'printer', title: 'Printer tidak ditemukan', body: 'Nyalakan Bluetooth, dekatkan printer, lalu cari ulang di menu Printer.' },
		{ icon: 'receipt-off', title: 'Struk pesanan tidak tercetak', body: 'Buka tab Stasiun dan Printer di halaman Cabang untuk melihat tablet mana yang mengirim struk stasiun itu, pasang printernya di menu Printer tablet tersebut, lalu ketuk Cetak ulang pada pemberitahuan di Papan Stasiun.' },
		{ icon: 'layout-kanban', title: 'Menu tidak muncul di stasiun', body: 'Pastikan stasiun itu sudah ditetapkan ke tablet ini di halaman Cabang, tab Perangkat.' },
		{ icon: 'cash-off', title: 'Tidak bisa membuka sesi', body: 'Hanya tablet dengan stasiun Kasir yang bisa membuka sesi. Tetapkan stasiun Kasir di halaman Cabang, tab Perangkat.' },
		{ icon: 'qrcode', title: 'QR ditolak', body: 'Tekan Pindai ulang di tablet, lalu pindai lagi dari HP.' },
		{ icon: 'cloud-upload', title: 'Pesanan tertahan', body: 'Pembuat pesanan memindai QR kembali supaya pesanannya terkirim.' },
		{ icon: 'logout', title: 'Tidak bisa keluar', body: 'Tutup sesi kasir dulu dan tunggu semua pesanan terkirim. Bila sesi belum terbaca, sambungkan internet.' },
		{ icon: 'clipboard-off', title: 'Menu Stok Opname tidak ada', body: 'Menu ini hanya tampil untuk peran dengan izin Tutup periode. Minta admin mencentangnya di Peran dan Izin.' },
		{ icon: 'package-off', title: 'Menu Bahan habis setelah tutup periode', body: 'Seluruh stok bahan kembali 0 saat periode ditutup. Admin mengisi Stok awal di web, menu Stok Opname.' },
		{ icon: 'notes-off', title: 'Tidak ada menu Catatan Pesanan', body: 'Menu ini perlu izin Kelola referensi. Minta admin mencentangnya di Peran dan Izin.' },
		{ icon: 'cloud-off', title: 'Hitungan opname tidak tersimpan', body: 'Hitungan tersimpan otomatis sebagai draf. Bila muncul Draf belum tersimpan, periksa internet; Stok Opname butuh internet dan tidak masuk antrean Mode Offline.' },
		{ icon: 'download', title: 'Aplikasi meminta pembaruan', body: 'Unduh dan pasang versi terbaru hanya dari halaman ini.' }
	]
};

export const ATTENDANCE_GUIDE: Guide = {
	title: 'Absen karyawan',
	intro: 'Absen dilakukan dari HP masing-masing: aplikasi Android atau aplikasi di layar utama iPhone. Setiap absen memakai foto dan lokasi.',
	topics: [
		{
			key: 'prepare',
			icon: 'device-mobile',
			title: 'Persiapan',
			who: 'Sekali di HP',
			steps: [
				step('download', 'Pasang aplikasi', 'Android memakai APK dari tab Android, iPhone dan iPad memasang lewat Safari dari tab iPhone dan iPad. Masuk dengan akun masing-masing.'),
				step('map-pin', 'Izinkan Lokasi', 'Saat diminta, ketuk Izinkan dan pilih lokasi tepat. Lokasi memastikan absen dilakukan di kafe.'),
				step('camera', 'Izinkan Kamera', 'Kamera dipakai untuk foto saat absen.'),
				step('gps', 'Nyalakan GPS', 'Layanan lokasi HP harus menyala. Halaman Izin diperlukan menunjukkan mana yang belum siap.')
			]
		},
		{
			key: 'clock-in',
			icon: 'login',
			title: 'Absen datang',
			who: 'Setiap shift',
			steps: [
				step('calendar', 'Cek jadwal hari ini', 'Buka Absen. Jadwal hari ini menampilkan kode shift, peran, dan cabang.'),
				step('clock', 'Tunggu jam bukanya', 'Absen datang dibuka 30 menit sebelum jam mulai sampai jam selesai shift. Setiap jadwal hanya bisa diabsen sekali.'),
				step('map-pin', 'Pastikan jaraknya', 'Layar menunjukkan jarak Anda ke cabang dan batasnya. Bila bertugas di tempat lain, pilih Saya bertugas di luar lokasi cabang dan isi catatan lokasi.'),
				step('camera', 'Foto dan kirim', 'Ketuk Absen datang, ambil foto, lalu Kirim absen. Foto diberi jam, tanggal, nama, cabang, dan jarak. Datang lewat batas toleransi ditandai Terlambat.')
			]
		},
		{
			key: 'self',
			icon: 'calendar-plus',
			title: 'Absen mandiri',
			who: 'Bila tidak ada jadwal',
			steps: [
				step('calendar-off', 'Tidak terdaftar di jadwal', 'Bila tidak ada jadwal yang bisa diabsen, ketuk Absen mandiri.'),
				step('building-store', 'Isi jadwal sendiri', 'Pilih Cabang, Peran, dan Kode shift. Kode shift yang muncul hanya yang jam mulainya dalam 30 menit dari sekarang dan tidak bertabrakan dengan jadwal lain. Isi alasan bila perlu, lalu Simpan jadwal.'),
				step('camera', 'Lanjutkan absen datang', 'Setelah jadwal tersimpan, ambil foto absen datang seperti biasa.')
			]
		},
		{
			key: 'clock-out',
			icon: 'logout',
			title: 'Absen pulang',
			who: 'Setiap selesai shift',
			steps: [
				step('camera', 'Absen pulang', 'Buka Absen, ketuk Absen pulang, ambil foto, lalu Kirim absen. Durasi kerja hari itu tampil setelah berhasil.'),
				step('clock-x', 'Lupa absen pulang', 'Bila tidak absen pulang sampai batas waktu setelah shift selesai, absen ditutup otomatis dan jam pulang diisi sistem. Pemberitahuannya muncul saat Absen dibuka.'),
				step('qrcode', 'Masuk ke tablet', 'Pada halaman Absen, bagian Perangkat operasional, ketuk Pindai QR untuk masuk ke tablet kafe.')
			]
		}
	],
	troubles: [
		{ icon: 'clock-pause', title: 'Ada shift tetapi belum bisa absen', body: 'Absen datang baru dibuka 30 menit sebelum jam mulai. Jam bukanya tertulis di halaman Absen.' },
		{ icon: 'calendar-x', title: 'Jadwal sudah dipakai atau berakhir', body: 'Setiap jadwal hanya bisa diabsen sekali dan tidak bisa diabsen setelah jam selesai. Hubungi atasan bila jadwalnya salah.' },
		{ icon: 'door-exit', title: 'Masih ada absen yang belum ditutup', body: 'Absen pulang dulu untuk jadwal sebelumnya, baru absen datang lagi.' },
		{ icon: 'map-pin-off', title: 'Lokasi belum terbaca', body: 'Nyalakan GPS, pindah ke tempat yang lebih terbuka, lalu ketuk Baca ulang lokasi.' },
		{ icon: 'lock', title: 'Peran tidak diizinkan absen sendiri', body: 'Kehadiran peran itu dicatat oleh admin. Hubungi atasan.' },
		{ icon: 'loader', title: 'Halaman absen memuat terus', body: 'Periksa internet, tutup lalu buka kembali aplikasinya. Di iPhone, ketuk Perbarui sekarang bila diminta.' }
	]
};

export const ANDROID_STEPS: string[] = ['Unduh APK', 'Izinkan dari sumber ini', 'Instal', 'Buka dan masuk'];

export const IOS_STEPS: string[] = ['Buka di Safari', 'Tekan Bagikan', 'Tambahkan ke Layar Utama', `Buka ${brand.name}`];
