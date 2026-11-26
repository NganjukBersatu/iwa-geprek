from app.core.permissions.model import Group, Permission, Section

GROUP = Group("people", "Orang", (
    Section("Akun dan peran", (
        Permission("web.masuk", "Masuk web admin", "Membuka web admin untuk pengelolaan dan laporan. Tanpa izin ini, akun hanya bisa memakai aplikasi karyawan dan perangkat operasional."),
        Permission("karyawan.kelola", "Kelola karyawan", "Menambah akun, mengubah peran, dan menempatkan di cabang."),
        Permission("peran.kelola", "Kelola peran dan izin", "Membuat peran baru dan menentukan izinnya. Izin ini bisa memberi izin lain."),
    )),
    Section("Jadwal", (
        Permission("jadwal.lihat", "Lihat papan jadwal", "Membuka papan Jadwal dan Kehadiran untuk melihat siapa jaga kapan (hanya baca; menyusun jadwal tetap lewat izin Susun jadwal).", default_for_new_role=True),
        Permission("jadwal.kelola", "Susun jadwal", "Menyusun jadwal kerja, bukan sekadar melihat."),
        Permission("kodeshift.kelola", "Kelola kode shift", "Menambah, mengubah, dan menghapus kode shift beserta jam kerja dan jam lemburnya."),
    )),
    Section("Kehadiran", (
        Permission("absensi.mandiri", "Absen mandiri", "Absen datang dan pulang sendiri dengan foto. Tanpa ini, absensi hanya bisa ditandai admin.", default_for_new_role=True),
        Permission("kehadiran.kelola", "Tandai dan koreksi kehadiran", "Menandai hadir/telat/izin dan membetulkan jam masuk-keluar yang salah."),
        Permission("lembur.mandiri", "Catat lembur sendiri", "Memakai tombol Mulai/Selesai lembur di halaman Absensi. Koreksi lembur orang lain tetap lewat izin Tandai dan koreksi kehadiran.", default_for_new_role=True),
    )),
    Section("Tugas dan SOP", (
        Permission("tugas.lihat", "Lihat dan lapor tugas", "Membuka papan Tugas untuk melapor pekerjaan sendiri.", default_for_new_role=True),
        Permission("tugas.kelola", "Kelola tugas", "Memberi tugas ke karyawan dan melihat pekerjaan semua orang. Untuk admin dan captain."),
        Permission("sop.kelola", "Kelola SOP", "Menulis, mengubah, menonaktifkan, dan menghapus SOP yang dibaca karyawan di aplikasi."),
    )),
))
