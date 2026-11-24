package id.kongstudio.cafe.feature.leave

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.leave_date_range
import id.kongstudio.cafe.resources.leave_status_approved
import id.kongstudio.cafe.resources.leave_status_pending
import id.kongstudio.cafe.resources.leave_status_rejected
import id.kongstudio.cafe.resources.leave_type_permit
import id.kongstudio.cafe.resources.leave_type_sick
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import org.jetbrains.compose.resources.stringResource

internal val LeaveStatus.tone: BadgeTone
    get() = when (this) {
        LeaveStatus.Pending -> BadgeTone.Warning
        LeaveStatus.Approved -> BadgeTone.Positive
        LeaveStatus.Rejected -> BadgeTone.Danger
    }

@Composable
internal fun leaveTypeLabel(type: LeaveType): String = stringResource(
    if (type == LeaveType.Sick) Res.string.leave_type_sick else Res.string.leave_type_permit,
)

@Composable
internal fun leaveStatusLabel(status: LeaveStatus): String = stringResource(
    when (status) {
        LeaveStatus.Pending -> Res.string.leave_status_pending
        LeaveStatus.Approved -> Res.string.leave_status_approved
        LeaveStatus.Rejected -> Res.string.leave_status_rejected
    },
)

/** Contoh: "12 Oktober 2026" untuk satu hari, "12 Oktober 2026 – 14 Oktober 2026" untuk rentang. */
@Composable
internal fun leaveRangeLabel(request: LeaveRequest): String {
    val start = longDateLabel(request.startDate)
    return if (request.startDate == request.endDate) {
        start
    } else {
        stringResource(Res.string.leave_date_range, start, longDateLabel(request.endDate))
    }
}
