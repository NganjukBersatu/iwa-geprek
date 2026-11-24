package id.kongstudio.cafe.feature.leave

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.leave_action
import id.kongstudio.cafe.resources.leave_empty
import id.kongstudio.cafe.resources.leave_title
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun LeaveSection(
    state: LeaveUiState,
    onRetry: () -> Unit,
    onSubmit: (form: LeaveForm, attachment: LeaveAttachment?, onSuccess: () -> Unit) -> Unit,
    onCancel: (id: String, onSuccess: () -> Unit) -> Unit,
    onClearError: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var requesting by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<LeaveRequest?>(null) }

    if (requesting) {
        LeaveRequestSheet(
            submitting = state.working,
            error = state.error,
            onSubmit = { form, attachment -> onSubmit(form, attachment) { requesting = false } },
            onDismiss = {
                onClearError()
                requesting = false
            },
        )
    }

    selected?.let { request ->
        LeaveDetailSheet(
            request = request,
            working = state.working,
            error = state.error,
            onCancel = { onCancel(request.id) { selected = null } },
            onDismiss = {
                onClearError()
                selected = null
            },
        )
    }

    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        SectionTitle(stringResource(Res.string.leave_title))
        PrimaryButton(text = stringResource(Res.string.leave_action), onClick = { requesting = true })

        if (state.failure != null) {
            FailureState(failure = state.failure!!, onRetry = onRetry)
        } else {
            StateListCard(
                loading = state.loading,
                empty = state.items.isEmpty(),
                emptyText = stringResource(Res.string.leave_empty),
            ) {
                DividedItems(state.items) { request ->
                    ListRow(
                        title = leaveTypeLabel(request.type),
                        detail = leaveRangeLabel(request),
                        caption = request.reason,
                        trailing = { LeaveStatusBadge(request.status) },
                        onClick = { selected = request },
                    )
                }
            }
        }
    }
}

@Composable
internal fun LeaveStatusBadge(status: LeaveStatus) {
    StatusBadge(text = leaveStatusLabel(status), tone = status.tone)
}
