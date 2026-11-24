package id.kongstudio.cafe.feature.attendancelog

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.status_absent
import id.kongstudio.cafe.resources.status_late
import id.kongstudio.cafe.resources.status_permit
import id.kongstudio.cafe.resources.status_present
import id.kongstudio.cafe.resources.status_sick
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun AttendanceStatusBadge(day: AttendanceDay) {
    val (text, tone) = when (day.status) {
        AttendanceStatus.Present -> stringResource(Res.string.status_present) to BadgeTone.Positive
        AttendanceStatus.Late ->
            stringResource(Res.string.status_late, day.lateMinutes.toString()) to BadgeTone.Warning
        AttendanceStatus.Permit -> stringResource(Res.string.status_permit) to BadgeTone.Neutral
        AttendanceStatus.Sick -> stringResource(Res.string.status_sick) to BadgeTone.Neutral
        AttendanceStatus.Absent -> stringResource(Res.string.status_absent) to BadgeTone.Danger
    }
    StatusBadge(text = text, tone = tone)
}
