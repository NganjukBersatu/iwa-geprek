package id.kongstudio.cafe.feature.attendance.selfschedule

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.self_schedule_intro_confirm
import id.kongstudio.cafe.resources.self_schedule_intro_message
import id.kongstudio.cafe.resources.self_schedule_intro_title
import id.kongstudio.cafe.resources.self_schedule_outlet
import id.kongstudio.cafe.resources.self_schedule_outlet_pick
import id.kongstudio.cafe.resources.self_schedule_reason
import id.kongstudio.cafe.resources.self_schedule_role
import id.kongstudio.cafe.resources.self_schedule_role_pick
import id.kongstudio.cafe.resources.self_schedule_shift
import id.kongstudio.cafe.resources.self_schedule_shift_empty
import id.kongstudio.cafe.resources.self_schedule_shift_label
import id.kongstudio.cafe.resources.self_schedule_shift_pick_outlet
import id.kongstudio.cafe.resources.self_schedule_submit
import id.kongstudio.cafe.resources.self_schedule_title
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import org.jetbrains.compose.resources.stringResource

/** Lembar absen mandiri sesuai langkahnya; tidak tampil bila tidak ada langkah yang terbuka. */
@Composable
internal fun SelfScheduleSheets(
    state: SelfScheduleUiState,
    onContinue: () -> Unit,
    onSelectOutlet: (String?) -> Unit,
    onSelectRole: (String?) -> Unit,
    onSelectShift: (String) -> Unit,
    onReasonChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onDismiss: () -> Unit,
) {
    when (state.step) {
        SelfScheduleStep.Intro -> ConfirmSheet(
            title = stringResource(Res.string.self_schedule_intro_title),
            message = stringResource(Res.string.self_schedule_intro_message),
            confirmLabel = stringResource(Res.string.self_schedule_intro_confirm),
            onConfirm = onContinue,
            onDismiss = onDismiss,
        )
        SelfScheduleStep.Form -> SelfScheduleForm(state, onSelectOutlet, onSelectRole, onSelectShift, onReasonChange, onSubmit, onDismiss)
        null -> Unit
    }
}

@Composable
private fun SelfScheduleForm(
    state: SelfScheduleUiState,
    onSelectOutlet: (String?) -> Unit,
    onSelectRole: (String?) -> Unit,
    onSelectShift: (String) -> Unit,
    onReasonChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onDismiss: () -> Unit,
) {
    val options = state.options
    val suggestions = if (state.outletId == null) emptyList() else options?.suggestions.orEmpty()

    FormSheet(
        title = stringResource(Res.string.self_schedule_title),
        submitLabel = stringResource(Res.string.self_schedule_submit),
        onSubmit = onSubmit,
        onDismiss = onDismiss,
        submitting = state.submitting,
        canSubmit = state.canSubmit,
        error = state.error?.resolve(),
        loadingOnSubmit = true,
    ) {
        DropdownField(
            label = stringResource(Res.string.self_schedule_outlet),
            options = choices(stringResource(Res.string.self_schedule_outlet_pick), options?.outlets.orEmpty()),
            selectedKey = state.outletId,
            onSelect = onSelectOutlet,
        )
        DropdownField(
            label = stringResource(Res.string.self_schedule_role),
            options = choices(stringResource(Res.string.self_schedule_role_pick), options?.roles.orEmpty()),
            selectedKey = state.roleId,
            onSelect = onSelectRole,
        )
        when {
            state.outletId == null -> Notice(stringResource(Res.string.self_schedule_shift_pick_outlet))
            state.loading -> Unit
            suggestions.isEmpty() -> Notice(stringResource(Res.string.self_schedule_shift_empty))
            else -> ChoiceFlow(
                label = stringResource(Res.string.self_schedule_shift),
                options = suggestions.map { shiftLabel(it) },
                selectedIndex = suggestions.indexOfFirst { it.shiftCodeId == state.shiftCodeId }.takeIf { it >= 0 },
                onSelect = { onSelectShift(suggestions[it].shiftCodeId) },
            )
        }
        AppTextField(
            value = state.reason,
            onValueChange = onReasonChange,
            label = stringResource(Res.string.self_schedule_reason),
            enabled = !state.submitting,
        )
    }
}

/** Pilihan pertama tanpa kunci menjadi ajakan memilih, karena isian ini belum punya nilai di awal. */
private fun choices(placeholder: String, items: List<SelfScheduleChoice>): List<DropdownOption> =
    listOf(DropdownOption(null, placeholder)) + items.map { DropdownOption(it.id, it.name) }

@Composable
private fun shiftLabel(suggestion: ShiftSuggestion): String {
    val start = suggestion.startsAt?.time
    val end = suggestion.endsAt?.time
    if (start == null || end == null) return suggestion.code
    return stringResource(Res.string.self_schedule_shift_label, suggestion.code, stringResource(Res.string.format_time_range, start, end))
}
