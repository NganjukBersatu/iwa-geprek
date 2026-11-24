package id.kongstudio.cafe.feature.overtime

import id.kongstudio.cafe.core.format.WibStamp

internal class OvertimeEntry(
    val id: String,
    val start: WibStamp?,
    val end: WibStamp?,
    val minutes: Int,
    /** True untuk lembur dari jadwal; false untuk yang dicatat sendiri. */
    val scheduled: Boolean,
    val note: String?,
)

/** Lembur dadakan yang diisi karyawan: mulai dan selesai bertanggal (WIB), serta alasan. */
internal class OvertimeRequest(
    val startDate: String,
    val startTime: String,
    val endDate: String,
    val endTime: String,
    val note: String,
)

internal const val OvertimePageSize = 10
