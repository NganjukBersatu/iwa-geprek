package id.kongstudio.cafe.feature.dayplan

import id.kongstudio.cafe.core.format.WibStamp

internal enum class SegmentKind { Work, ScheduledOvertime, UnplannedOvertime }

/** Satu rentang waktu hari ini milik karyawan, dengan jam nyata dalam detik epoch dan dalam WIB. */
internal class DaySegment(
    val kind: SegmentKind,
    val startEpoch: Long,
    val endEpoch: Long,
    val start: WibStamp,
    val end: WibStamp,
    val minutes: Int,
    val code: String?,
    val colorHex: String?,
) {
    val isOvertime: Boolean get() = kind != SegmentKind.Work
}

internal class DayPlan(
    /** Urut menurut jam mulai. */
    val segments: List<DaySegment>,
    /** Lembur terjadwal hari ini, bila ada; menghalangi pencatatan lembur dadakan. */
    val scheduledOvertime: DaySegment?,
)

/** Penghubung rencana hari ke bagian lain halaman: lembur terjadwal hari ini dan cara memuat ulang rencana. */
internal class DayPlanLink(
    val scheduledOvertime: DaySegment?,
    val reload: () -> Unit,
)
