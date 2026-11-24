package id.kongstudio.cafe.feature.tasks

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.tasks_filter_no_match
import id.kongstudio.cafe.resources.tasks_filter_person_search
import id.kongstudio.cafe.resources.tasks_form_assignee
import id.kongstudio.cafe.resources.tasks_form_assignee_pick
import id.kongstudio.cafe.resources.tasks_form_description
import id.kongstudio.cafe.resources.tasks_form_done
import id.kongstudio.cafe.resources.tasks_form_due_date
import id.kongstudio.cafe.resources.tasks_form_due_time
import id.kongstudio.cafe.resources.tasks_form_due_toggle
import id.kongstudio.cafe.resources.tasks_form_mode_employee
import id.kongstudio.cafe.resources.tasks_form_mode_self
import id.kongstudio.cafe.resources.tasks_form_name
import id.kongstudio.cafe.resources.tasks_form_outlet
import id.kongstudio.cafe.resources.tasks_form_outlet_pick
import id.kongstudio.cafe.resources.tasks_form_submit
import id.kongstudio.cafe.resources.tasks_form_assignee_required
import id.kongstudio.cafe.resources.tasks_form_outlet_required
import id.kongstudio.cafe.resources.tasks_form_title
import id.kongstudio.cafe.resources.tasks_form_title_required
import id.kongstudio.cafe.resources.tasks_proof_required
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.mediafield.MediaField
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia
import id.kongstudio.cafe.ui.component.optionaldatetime.DateTimeValue
import id.kongstudio.cafe.ui.component.optionaldatetime.OptionalDateTimeField
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import org.jetbrains.compose.resources.stringResource

private enum class FormMode { Self, Employee }

/** Lembar tugas baru: karyawan menulis untuk dirinya sendiri, sedangkan pengelola juga bisa memberi tugas ke karyawan. */
@Composable
internal fun TaskFormSheet(
    options: TaskOptions?,
    submitting: Boolean,
    error: UiText?,
    onSubmit: (NewTask) -> Unit,
    onLoadOptions: (outletId: String?) -> Unit,
    onDismiss: () -> Unit,
) {
    val canManage = options?.canManage == true
    val outlets = options?.outlets.orEmpty()
    val assignees = options?.assignees.orEmpty()
    val modes = FormMode.entries

    var mode by remember { mutableStateOf(FormMode.Self) }
    var outletIndex by remember { mutableStateOf<Int?>(null) }
    var assigneeIndex by remember { mutableStateOf<Int?>(null) }
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var due by remember { mutableStateOf<DateTimeValue?>(null) }
    var media by remember { mutableStateOf<List<PickedMedia>>(emptyList()) }
    var done by remember { mutableStateOf(false) }

    val choosesOutlet = canManage && mode == FormMode.Employee && outlets.size > 1
    val finishable = mode == FormMode.Self
    val valid = title.isNotBlank() &&
        (mode != FormMode.Employee || assigneeIndex != null) &&
        (!choosesOutlet || outletIndex != null) &&
        (!done || media.isNotEmpty())

    FormSheet(
        title = stringResource(Res.string.tasks_form_title),
        submitLabel = stringResource(Res.string.tasks_form_submit),
        onSubmit = {
            onSubmit(
                NewTask(
                    title = title,
                    description = description,
                    assigneeId = assigneeIndex?.takeIf { mode == FormMode.Employee }?.let { assignees[it].id },
                    due = due?.toIso(),
                    complete = done && finishable,
                    media = media,
                ),
            )
        },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = valid,
        invalidMessage = when {
            title.isBlank() -> stringResource(Res.string.tasks_form_title_required)
            mode == FormMode.Employee && assigneeIndex == null -> stringResource(Res.string.tasks_form_assignee_required)
            choosesOutlet && outletIndex == null -> stringResource(Res.string.tasks_form_outlet_required)
            else -> stringResource(Res.string.tasks_proof_required)
        },
        error = error?.resolve(),
        loadingOnSubmit = true,
    ) {
        if (canManage) {
            SegmentedControl(
                options = listOf(
                    stringResource(Res.string.tasks_form_mode_self),
                    stringResource(Res.string.tasks_form_mode_employee),
                ),
                selectedIndex = modes.indexOf(mode),
                onSelect = {
                    mode = modes[it]
                    done = false
                },
            )
        }
        if (choosesOutlet) {
            // Dropdown, bukan deretan chip: daftar cabang dan karyawan bisa panjang dan tidak boleh memenuhi lembar.
            DropdownField(
                label = stringResource(Res.string.tasks_form_outlet),
                // Pilihan kosong di depan, supaya kolom tidak menampilkan cabang pertama seolah sudah dipilih.
                options = listOf(DropdownOption(key = null, label = stringResource(Res.string.tasks_form_outlet_pick))) +
                    outlets.map { DropdownOption(key = it.id, label = it.name) },
                selectedKey = outletIndex?.let { outlets.getOrNull(it)?.id },
                onSelect = { id ->
                    val index = outlets.indexOfFirst { it.id == id }.takeIf { it >= 0 }
                    if (index != outletIndex) {
                        outletIndex = index
                        assigneeIndex = null
                        if (index != null) onLoadOptions(outlets[index].id)
                    }
                },
            )
        }
        if (mode == FormMode.Employee) {
            DropdownField(
                label = stringResource(Res.string.tasks_form_assignee),
                options = listOf(DropdownOption(key = null, label = stringResource(Res.string.tasks_form_assignee_pick))) +
                    assignees.map { DropdownOption(key = it.id, label = it.name) },
                selectedKey = assigneeIndex?.let { assignees.getOrNull(it)?.id },
                onSelect = { id -> assigneeIndex = assignees.indexOfFirst { it.id == id }.takeIf { it >= 0 } },
                searchLabel = stringResource(Res.string.tasks_filter_person_search),
                emptyText = stringResource(Res.string.tasks_filter_no_match),
            )
        }
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
        )
        MediaField(items = media, onChange = { media = it }, enabled = !submitting)
        if (finishable) {
            ToggleSwitch(
                label = stringResource(Res.string.tasks_form_done),
                checked = done,
                onCheckedChange = { done = it },
            )
        }
    }
}
