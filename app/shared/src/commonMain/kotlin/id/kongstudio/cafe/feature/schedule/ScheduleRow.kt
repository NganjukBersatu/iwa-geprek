package id.kongstudio.cafe.feature.schedule

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_detail_pair
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.schedule_as_role
import id.kongstudio.cafe.resources.schedule_day_off
import id.kongstudio.cafe.resources.schedule_mine
import id.kongstudio.cafe.resources.schedule_overtime_total
import id.kongstudio.cafe.ui.component.shiftrow.ShiftRow
import id.kongstudio.cafe.ui.theme.color.parseHexColor
import org.jetbrains.compose.resources.stringResource

/** Satu penugasan jadwal; [showUser] menjadikan nama staf judulnya dan jam di keterangan. */
@Composable
internal fun ScheduleRow(item: ScheduleItem, showUser: Boolean) {
    val code = item.code
    val hours = if (item.off) {
        stringResource(Res.string.schedule_day_off)
    } else if (code?.start != null && code.end != null) {
        stringResource(Res.string.format_time_range, code.start, code.end)
    } else {
        code?.code.orEmpty()
    }
    val role = item.roleName?.let { stringResource(Res.string.schedule_as_role, it) }

    val note = item.note?.takeIf { it.isNotBlank() }
    val session = code?.category?.let { stringResource(Res.string.format_detail_pair, it, hours) } ?: hours
    val caption = if (note != null) stringResource(Res.string.format_detail_pair, session, note) else session

    val overtime = if (!item.off && code?.overtimeStart != null && code.overtimeEnd != null) {
        stringResource(
            Res.string.schedule_overtime_total,
            stringResource(Res.string.format_time_range, code.overtimeStart, code.overtimeEnd),
            durationLabel(DateTimeFormat.spanMinutes(code.overtimeStart, code.overtimeEnd)),
        )
    } else {
        null
    }

    ShiftRow(
        title = if (showUser) item.userName else session,
        detail = role,
        caption = if (showUser) caption else note,
        footnote = overtime,
        code = code?.code,
        codeColor = parseHexColor(code?.color),
        tag = if (showUser && item.mine) stringResource(Res.string.schedule_mine) else null,
    )
}
