package id.kongstudio.cafe.feature.attendancelog

import kotlin.math.roundToInt
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.resources.attendance_detail_distance_value
import id.kongstudio.cafe.resources.attendance_detail_distance_limit
import id.kongstudio.cafe.resources.attendance_detail_accuracy_value
import id.kongstudio.cafe.core.format.DateTimeFormat
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_detail_accuracy_in
import id.kongstudio.cafe.resources.attendance_detail_accuracy_out
import id.kongstudio.cafe.resources.attendance_detail_auto_closed
import id.kongstudio.cafe.resources.attendance_detail_clock_in
import id.kongstudio.cafe.resources.attendance_detail_clock_out
import id.kongstudio.cafe.resources.attendance_detail_date
import id.kongstudio.cafe.resources.attendance_detail_distance_in
import id.kongstudio.cafe.resources.attendance_detail_distance_out
import id.kongstudio.cafe.resources.attendance_detail_late
import id.kongstudio.cafe.resources.attendance_detail_late_value
import id.kongstudio.cafe.resources.attendance_detail_location_in
import id.kongstudio.cafe.resources.attendance_detail_location_out
import id.kongstudio.cafe.resources.attendance_detail_none
import id.kongstudio.cafe.resources.attendance_detail_note
import id.kongstudio.cafe.resources.attendance_detail_outside_in
import id.kongstudio.cafe.resources.attendance_detail_outside_out
import id.kongstudio.cafe.resources.attendance_detail_penalty
import id.kongstudio.cafe.resources.attendance_detail_photo_in
import id.kongstudio.cafe.resources.attendance_detail_photo_out
import id.kongstudio.cafe.resources.attendance_detail_reason
import id.kongstudio.cafe.resources.attendance_detail_role
import id.kongstudio.cafe.resources.attendance_detail_shift
import id.kongstudio.cafe.resources.attendance_detail_status
import id.kongstudio.cafe.resources.attendance_detail_title
import id.kongstudio.cafe.resources.attendance_detail_work
import id.kongstudio.cafe.resources.format_date_long
import id.kongstudio.cafe.resources.format_duration
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.weekdays_long
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.detaillist.DetailList
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.photopair.PhotoItem
import id.kongstudio.cafe.ui.component.photopair.PhotoPair
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

/** Detail satu hari kehadiran; baris yang tidak punya nilai tidak ditampilkan. */
@Composable
internal fun AttendanceDetailSheet(
    day: AttendanceDay,
    onDismiss: () -> Unit,
) {
    val weekdays = stringArrayResource(Res.array.weekdays_long)
    val months = stringArrayResource(Res.array.months)
    val none = stringResource(Res.string.attendance_detail_none)

    val date = stringResource(
        Res.string.format_date_long,
        weekdays[DateTimeFormat.weekdayIndex(day.date)],
        DateTimeFormat.dayOfMonth(day.date),
        months[DateTimeFormat.monthIndex(day.date)],
        day.date.take(4),
    )
    val work = day.workMinutes?.let {
        val (hours, minutes) = DateTimeFormat.durationParts(it)
        stringResource(Res.string.format_duration, hours, minutes)
    }
    val distanceIn = distanceLabel(day.distanceIn, day.radiusIn)
    val distanceOut = distanceLabel(day.distanceOut, day.radiusOut)
    val accuracyIn = accuracyLabel(day.accuracyIn)
    val accuracyOut = accuracyLabel(day.accuracyOut)
    val clockOut = DateTimeFormat.clock(day.clockOut) ?: none

    val rows = buildList<@Composable () -> Unit> {
        add { DetailRow(stringResource(Res.string.attendance_detail_date), value = date) }
        add {
            DetailRow(
                stringResource(Res.string.attendance_detail_status),
                valueContent = { AttendanceStatusBadge(day) },
            )
        }
        day.shiftCode?.let { code ->
            add { DetailRow(stringResource(Res.string.attendance_detail_shift), value = code) }
        }
        day.roleName?.let { role ->
            add { DetailRow(stringResource(Res.string.attendance_detail_role), value = role) }
        }
        add {
            DetailRow(
                stringResource(Res.string.attendance_detail_clock_in),
                value = DateTimeFormat.clock(day.clockIn) ?: none,
            )
        }
        add {
            if (day.autoClosed) {
                DetailRow(
                    stringResource(Res.string.attendance_detail_clock_out),
                    valueContent = {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
                        ) {
                            AppText(
                                text = clockOut,
                                role = TextRole.Body,
                                color = AppTheme.colors.content,
                            )
                            StatusBadge(
                                text = stringResource(Res.string.attendance_detail_auto_closed),
                                tone = BadgeTone.Warning,
                            )
                        }
                    },
                )
            } else {
                DetailRow(stringResource(Res.string.attendance_detail_clock_out), value = clockOut)
            }
        }
        if (work != null) {
            add { DetailRow(stringResource(Res.string.attendance_detail_work), value = work) }
        }
        if (day.lateMinutes > 0) {
            add {
                DetailRow(
                    stringResource(Res.string.attendance_detail_late),
                    value = stringResource(Res.string.attendance_detail_late_value, day.lateMinutes.toString()),
                )
            }
        }
        if (day.penalty > 0) {
            add {
                DetailRow(
                    stringResource(Res.string.attendance_detail_penalty),
                    value = formatRupiah(day.penalty),
                )
            }
        }
        if (distanceIn != null) {
            add { DetailRow(stringResource(Res.string.attendance_detail_distance_in), value = distanceIn) }
        }
        if (accuracyIn != null) {
            add { DetailRow(stringResource(Res.string.attendance_detail_accuracy_in), value = accuracyIn) }
        }
        locationRow(day.modeIn, day.locationNoteIn, none, Res.string.attendance_detail_outside_in, Res.string.attendance_detail_location_in)
            ?.let { add(it) }
        if (distanceOut != null) {
            add { DetailRow(stringResource(Res.string.attendance_detail_distance_out), value = distanceOut) }
        }
        if (accuracyOut != null) {
            add { DetailRow(stringResource(Res.string.attendance_detail_accuracy_out), value = accuracyOut) }
        }
        locationRow(day.modeOut, day.locationNoteOut, none, Res.string.attendance_detail_outside_out, Res.string.attendance_detail_location_out)
            ?.let { add(it) }
        day.outsideScheduleReason?.takeIf { it.isNotBlank() }?.let { reason ->
            add { DetailRow(stringResource(Res.string.attendance_detail_reason), value = reason) }
        }
        day.note?.takeIf { it.isNotBlank() }?.let { note ->
            add { DetailRow(stringResource(Res.string.attendance_detail_note), value = note) }
        }
    }

    AppBottomSheet(
        title = stringResource(Res.string.attendance_detail_title),
        onDismiss = onDismiss,
    ) {
        DetailList(rows)
        PhotoPair(
            first = PhotoItem(day.photoInUrl, stringResource(Res.string.attendance_detail_photo_in)),
            second = PhotoItem(day.photoOutUrl, stringResource(Res.string.attendance_detail_photo_out)),
            modifier = Modifier.padding(top = AppTheme.spacing.lg),
        )
    }
}

@Composable
private fun distanceLabel(distance: Double?, radius: Int?): String? {
    if (distance == null) return null
    val meters = distance.roundToInt().toString()
    return if (radius != null) {
        stringResource(Res.string.attendance_detail_distance_limit, meters, radius.toString())
    } else {
        stringResource(Res.string.attendance_detail_distance_value, meters)
    }
}

@Composable
private fun accuracyLabel(accuracy: Double?): String? =
    accuracy?.let { stringResource(Res.string.attendance_detail_accuracy_value, it.roundToInt().toString()) }

/** Baris keterangan lokasi: di luar lokasi memakai label peringatan, selain itu hanya bila ada catatan. */
private fun locationRow(
    mode: String?,
    note: String?,
    none: String,
    outsideLabel: org.jetbrains.compose.resources.StringResource,
    noteLabel: org.jetbrains.compose.resources.StringResource,
): (@Composable () -> Unit)? {
    val text = note?.takeIf { it.isNotBlank() }
    return when {
        mode == LOCATION_MODE_OUTSIDE -> { { DetailRow(stringResource(outsideLabel), value = text ?: none) } }
        text != null -> { { DetailRow(stringResource(noteLabel), value = text) } }
        else -> null
    }
}
