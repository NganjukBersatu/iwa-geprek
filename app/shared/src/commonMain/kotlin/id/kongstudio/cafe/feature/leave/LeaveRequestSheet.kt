package id.kongstudio.cafe.feature.leave

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.leave_action
import id.kongstudio.cafe.resources.leave_date_invalid
import id.kongstudio.cafe.resources.leave_end
import id.kongstudio.cafe.resources.leave_link
import id.kongstudio.cafe.resources.leave_pdf_pick
import id.kongstudio.cafe.resources.leave_pdf_remove
import id.kongstudio.cafe.resources.leave_pdf_selected
import id.kongstudio.cafe.resources.leave_reason
import id.kongstudio.cafe.resources.leave_start
import id.kongstudio.cafe.resources.leave_submit
import id.kongstudio.cafe.resources.leave_type
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.datefield.DateField
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pdfpicker.PickedPdf
import id.kongstudio.cafe.ui.component.pdfpicker.rememberPdfPicker
import id.kongstudio.cafe.ui.component.photosubmitform.PhotoSubmitForm
import id.kongstudio.cafe.ui.component.sourcebutton.SourceButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Lembar mengajukan izin atau sakit; lampiran berupa foto atau PDF, atau bila tanpa lampiran, tautan. */
@Composable
internal fun LeaveRequestSheet(
    submitting: Boolean,
    error: UiText?,
    onSubmit: (form: LeaveForm, attachment: LeaveAttachment?) -> Unit,
    onDismiss: () -> Unit,
) {
    val today = remember { DateTimeFormat.todayWib() }
    var type by remember { mutableStateOf(LeaveType.Permit) }
    var start by remember { mutableStateOf(today) }
    var end by remember { mutableStateOf(today) }
    var reason by remember { mutableStateOf("") }
    var link by remember { mutableStateOf("") }
    var pdf by remember { mutableStateOf<PickedPdf?>(null) }
    val pdfPicker = rememberPdfPicker(onPicked = { pdf = it })

    val types = LeaveType.entries
    val datesValid = end >= start
    val localError = if (datesValid) null else stringResource(Res.string.leave_date_invalid)

    AppBottomSheet(title = stringResource(Res.string.leave_action), onDismiss = onDismiss) {
        PhotoSubmitForm(
            submitLabel = stringResource(Res.string.leave_submit),
            onSubmit = { photo ->
                // PDF yang dipilih menggantikan foto sebagai lampiran.
                val attachment = pdf?.let { LeaveAttachment.pdf(it.bytes) } ?: photo?.let(LeaveAttachment::photo)
                onSubmit(LeaveForm(type, start, end, reason, link), attachment)
            },
            submitting = submitting,
            canSubmit = datesValid && reason.isNotBlank(),
            photoRequired = link.isBlank() && pdf == null,
            error = localError ?: error?.resolve(),
        ) {
            ChoiceGroup(
                label = stringResource(Res.string.leave_type),
                options = types.map { leaveTypeLabel(it) },
                selectedIndex = types.indexOf(type),
                onSelect = { type = types[it] },
            )
            DateField(
                label = stringResource(Res.string.leave_start),
                value = start,
                today = today,
                enabled = !submitting,
                onValueChange = {
                    start = it
                    if (end < it) end = it
                },
            )
            DateField(
                label = stringResource(Res.string.leave_end),
                value = end,
                today = today,
                enabled = !submitting,
                onValueChange = { end = it },
            )
            AppTextField(
                value = reason,
                onValueChange = { reason = it },
                label = stringResource(Res.string.leave_reason),
                enabled = !submitting,
            )
            AppTextField(
                value = link,
                onValueChange = { link = it },
                label = stringResource(Res.string.leave_link),
                enabled = !submitting,
            )
            SourceButton(
                label = stringResource(if (pdf == null) Res.string.leave_pdf_pick else Res.string.leave_pdf_remove),
                icon = AppIcons.FileText,
                onClick = { if (pdf == null) pdfPicker.pick() else pdf = null },
                enabled = !submitting,
                modifier = Modifier.fillMaxWidth(),
            )
            pdf?.let { Notice(stringResource(Res.string.leave_pdf_selected, it.name)) }
        }
    }
}
