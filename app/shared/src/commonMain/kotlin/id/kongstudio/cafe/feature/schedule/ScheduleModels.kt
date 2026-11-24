package id.kongstudio.cafe.feature.schedule

internal class ShiftCode(
    val id: String,
    val code: String,
    /** Nama kategori kode, misalnya nama sesi kerja. */
    val category: String?,
    /** Jam "HH:MM"; kosong untuk kode libur. */
    val start: String?,
    val end: String?,
    /** Jendela lembur "HH:MM", bila kode memilikinya. */
    val overtimeStart: String?,
    val overtimeEnd: String?,
    /** Warna hex pilihan admin. */
    val color: String?,
    val off: Boolean,
)

/** Jadwal satu bulan beserta nama cabangnya. */
internal class ScheduleMonth(
    val items: List<ScheduleItem>,
    val outletName: String?,
)

internal class ScheduleItem(
    /** Tanggal "YYYY-MM-DD". */
    val date: String,
    val code: ShiftCode?,
    /** Penugasan peran pada hari itu. */
    val roleName: String?,
    val note: String?,
    val off: Boolean,
    val userId: String,
    val userName: String,
    /** Milik pengguna yang sedang masuk. */
    val mine: Boolean,
)
