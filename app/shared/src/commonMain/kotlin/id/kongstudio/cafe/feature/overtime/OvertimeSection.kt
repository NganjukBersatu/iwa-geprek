package id.kongstudio.cafe.feature.overtime

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.feature.dayplan.DaySegment
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.overtime_empty
import id.kongstudio.cafe.resources.overtime_history
import id.kongstudio.cafe.resources.overtime_kind_scheduled
import id.kongstudio.cafe.resources.overtime_kind_unplanned
import id.kongstudio.cafe.resources.overtime_start
import id.kongstudio.cafe.resources.overtime_title
import id.kongstudio.cafe.resources.overtime_unplanned_back
import id.kongstudio.cafe.resources.overtime_unplanned_blocked
import id.kongstudio.cafe.resources.overtime_unplanned_continue
import id.kongstudio.cafe.resources.overtime_unplanned_message
import id.kongstudio.cafe.resources.overtime_unplanned_title
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun OvertimeSection(
    state: OvertimeUiState,
    canRecord: Boolean,
    scheduledOvertime: DaySegment?,
    onRetry: () -> Unit,
    onRecord: (request: OvertimeRequest, onSuccess: () -> Unit) -> Unit,
    onPageChange: (Int) -> Unit,
    onClearError: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var noticing by remember { mutableStateOf(false) }
    var recording by remember { mutableStateOf(false) }

    if (noticing) {
        ConfirmSheet(
            title = stringResource(Res.string.overtime_unplanned_title),
            message = if (scheduledOvertime == null) {
                stringResource(Res.string.overtime_unplanned_message)
            } else {
                stringResource(
                    Res.string.overtime_unplanned_blocked,
                    stringResource(
                        Res.string.format_time_range,
                        scheduledOvertime.start.time,
                        scheduledOvertime.end.time,
                    ),
                )
            },
            confirmLabel = stringResource(Res.string.overtime_unplanned_continue),
            dismissLabel = stringResource(Res.string.overtime_unplanned_back),
            confirmEnabled = scheduledOvertime == null,
            onConfirm = {
                noticing = false
                recording = true
            },
            onDismiss = { noticing = false },
        )
    }

    if (recording) {
        OvertimeFormSheet(
            submitting = state.working,
            error = state.error,
            onSubmit = { request -> onRecord(request) { recording = false } },
            onDismiss = {
                onClearError()
                recording = false
            },
        )
    }

    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        SectionTitle(stringResource(Res.string.overtime_title))

        if (canRecord) {
            PrimaryButton(text = stringResource(Res.string.overtime_start), onClick = { noticing = true })
        }

        when {
            state.loading -> LoadingState(rows = 2)

            state.failure != null -> FailureState(failure = state.failure, onRetry = onRetry)

            else -> {
                SectionTitle(stringResource(Res.string.overtime_history))
                PagedListCard(
                    items = state.pageEntries,
                    page = state.page,
                    pageCount = state.pageCount,
                    onPageChange = onPageChange,
                    emptyText = stringResource(Res.string.overtime_empty),
                ) { entry -> OvertimeRow(entry) }
            }
        }
    }
}

@Composable
private fun OvertimeRow(entry: OvertimeEntry) {
    val start = entry.start
    val end = entry.end

    ListRow(
        title = start?.let { whenLabel(it) }.orEmpty(),
        detail = if (start != null && end != null) {
            stringResource(Res.string.format_time_range, start.time, end.time)
        } else {
            null
        },
        caption = entry.note,
        footnote = stringResource(if (entry.scheduled) Res.string.overtime_kind_scheduled else Res.string.overtime_kind_unplanned),
        trailing = { StatusBadge(text = durationLabel(entry.minutes), tone = BadgeTone.Positive) },
    )
}
