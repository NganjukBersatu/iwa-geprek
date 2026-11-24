package id.kongstudio.cafe.feature.overtime

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.overtime_form_end_date
import id.kongstudio.cafe.resources.overtime_form_end_time
import id.kongstudio.cafe.resources.overtime_form_note
import id.kongstudio.cafe.resources.overtime_form_order_invalid
import id.kongstudio.cafe.resources.overtime_form_start_date
import id.kongstudio.cafe.resources.overtime_form_start_time
import id.kongstudio.cafe.resources.overtime_form_submit
import id.kongstudio.cafe.resources.overtime_form_title
import id.kongstudio.cafe.ui.component.datefield.DateField
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.timefield.TimeField
import org.jetbrains.compose.resources.stringResource

private const val DefaultSpanSeconds = 3_600L

/** Lembar mencatat lembur di luar jadwal: mulai dan selesai bertanggal, serta alasan yang wajib diisi. */
@Composable
internal fun OvertimeFormSheet(
    submitting: Boolean,
    error: UiText?,
    onSubmit: (OvertimeRequest) -> Unit,
    onDismiss: () -> Unit,
) {
    val today = remember { DateTimeFormat.todayWib() }
    val begin = remember { DateTimeFormat.stampAt(ServerClock.nowEpochSeconds()) }
    val finish = remember { DateTimeFormat.stampAt(ServerClock.nowEpochSeconds() + DefaultSpanSeconds) }
    var startDate by remember { mutableStateOf(begin.date) }
    var startTime by remember { mutableStateOf(begin.time) }
    var endDate by remember { mutableStateOf(finish.date) }
    var endTime by remember { mutableStateOf(finish.time) }
    var note by remember { mutableStateOf("") }

    val orderValid = "$endDate $endTime" > "$startDate $startTime"

    FormSheet(
        title = stringResource(Res.string.overtime_form_title),
        submitLabel = stringResource(Res.string.overtime_form_submit),
        onSubmit = { onSubmit(OvertimeRequest(startDate, startTime, endDate, endTime, note)) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = orderValid && note.isNotBlank(),
        error = if (orderValid) error?.resolve() else stringResource(Res.string.overtime_form_order_invalid),
        loadingOnSubmit = true,
    ) {
        DateField(
            label = stringResource(Res.string.overtime_form_start_date),
            value = startDate,
            today = today,
            enabled = !submitting,
            onValueChange = { startDate = it },
        )
        TimeField(
            label = stringResource(Res.string.overtime_form_start_time),
            value = startTime,
            enabled = !submitting,
            onValueChange = { startTime = it },
        )
        DateField(
            label = stringResource(Res.string.overtime_form_end_date),
            value = endDate,
            today = today,
            enabled = !submitting,
            onValueChange = { endDate = it },
        )
        TimeField(
            label = stringResource(Res.string.overtime_form_end_time),
            value = endTime,
            enabled = !submitting,
            onValueChange = { endTime = it },
        )
        AppTextField(
            value = note,
            onValueChange = { note = it },
            label = stringResource(Res.string.overtime_form_note),
            enabled = !submitting,
        )
    }
}
