package id.kongstudio.cafe.feature.tasks

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.tasks_edit_submit
import id.kongstudio.cafe.resources.tasks_edit_title
import id.kongstudio.cafe.resources.tasks_form_description
import id.kongstudio.cafe.resources.tasks_form_due_date
import id.kongstudio.cafe.resources.tasks_form_due_time
import id.kongstudio.cafe.resources.tasks_form_due_toggle
import id.kongstudio.cafe.resources.tasks_form_name
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.optionaldatetime.DateTimeValue
import id.kongstudio.cafe.ui.component.optionaldatetime.OptionalDateTimeField
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import org.jetbrains.compose.resources.stringResource

/** Lembar mengubah judul, keterangan, dan batas waktu tugas yang dibuat sendiri. */
@Composable
internal fun TaskEditSheet(
    task: TaskItem,
    submitting: Boolean,
    error: UiText?,
    onSubmit: (title: String, description: String, due: DateTimeValue?) -> Unit,
    onDismiss: () -> Unit,
) {
    var title by remember { mutableStateOf(task.title) }
    var description by remember { mutableStateOf(task.description.orEmpty()) }
    var due by remember { mutableStateOf(task.due?.let { DateTimeValue(it.date, it.time) }) }

    FormSheet(
        title = stringResource(Res.string.tasks_edit_title),
        submitLabel = stringResource(Res.string.tasks_edit_submit),
        onSubmit = { onSubmit(title, description, due) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = title.isNotBlank(),
        error = error?.resolve(),
        loadingOnSubmit = true,
    ) {
        AppTextField(
            value = title,
            onValueChange = { title = it },
            label = stringResource(Res.string.tasks_form_name),
            enabled = !submitting,
        )
        AppTextField(
            value = description,
            onValueChange = { description = it },
            label = stringResource(Res.string.tasks_form_description),
            enabled = !submitting,
        )
        OptionalDateTimeField(
            toggleLabel = stringResource(Res.string.tasks_form_due_toggle),
            dateLabel = stringResource(Res.string.tasks_form_due_date),
            timeLabel = stringResource(Res.string.tasks_form_due_time),
            value = due,
            onChange = { due = it },
            enabled = !submitting,
            removable = task.due == null,
        )
    }
}
