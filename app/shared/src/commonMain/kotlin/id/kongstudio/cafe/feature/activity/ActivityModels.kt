package id.kongstudio.cafe.feature.activity

import id.kongstudio.cafe.core.format.WibStamp

/** Penyaring jenis aktivitas; [key] adalah nilai yang dipahami server, null berarti semua. */
internal enum class ActivityGroup(val key: String?) {
    All(null),
    Attendance("attendance"),
    Task("task"),
    Overtime("overtime"),
    Leave("leave"),
    Operations("operations"),
}

internal enum class ActivityAction(val key: String) {
    ClockIn("clock_in"),
    ClockOut("clock_out"),
    TaskDone("task_done"),
    OvertimeRecorded("overtime_recorded"),
    LeaveRequested("leave_requested"),
    LeaveDecided("leave_decided"),
    OrderCreated("order_created"),
    OrderVoided("order_voided"),
    CashOpened("cash_opened"),
    CashClosed("cash_closed"),
}

internal class ActivityEvent(
    val id: String,
    val action: ActivityAction,
    val at: WibStamp,
    /** Judul tugas, nomor nota, kode shift, atau jenis izin, tergantung aktivitasnya. */
    val subject: String?,
    /** Status kehadiran, keputusan izin, atau "auto" untuk absen pulang otomatis. */
    val status: String?,
    val minutes: Int?,
)
