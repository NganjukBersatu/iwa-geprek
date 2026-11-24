package id.kongstudio.cafe.feature.attendance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.feature.dayplan.DayPlan
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_action_in
import id.kongstudio.cafe.resources.attendance_action_out
import id.kongstudio.cafe.resources.attendance_clock_in
import id.kongstudio.cafe.resources.attendance_clock_out
import id.kongstudio.cafe.resources.attendance_detail_auto_closed
import id.kongstudio.cafe.resources.attendance_detail_photo_in
import id.kongstudio.cafe.resources.attendance_detail_photo_out
import id.kongstudio.cafe.resources.attendance_detail_status
import id.kongstudio.cafe.resources.attendance_late_badge
import id.kongstudio.cafe.resources.attendance_block_already_used
import id.kongstudio.cafe.resources.attendance_block_ended
import id.kongstudio.cafe.resources.attendance_block_no_permission
import id.kongstudio.cafe.resources.attendance_block_no_schedule
import id.kongstudio.cafe.resources.attendance_block_not_open_yet
import id.kongstudio.cafe.resources.attendance_no_schedule
import id.kongstudio.cafe.resources.attendance_status_in
import id.kongstudio.cafe.resources.attendance_status_none
import id.kongstudio.cafe.resources.attendance_status_out
import id.kongstudio.cafe.resources.attendance_today_schedule
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.self_schedule_saved
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.photopair.PhotoItem
import id.kongstudio.cafe.ui.component.photopair.PhotoPair
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.shiftrow.ShiftRow
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.color.parseHexColor
import org.jetbrains.compose.resources.stringResource

private const val NO_VALUE = "—"

@Composable
internal fun AttendanceScreen(
    state: AttendanceUiState,
    onRetry: () -> Unit,
    onClock: (ClockKind) -> Unit,
    onAcknowledge: () -> Unit,
    onSubmit: (photo: ByteArray, outside: Boolean, note: String) -> Unit,
    onDismissSheet: () -> Unit,
    onFinishCelebration: () -> Unit,
    onSelfSchedule: () -> Unit,
    onRelocate: () -> Unit,
    previewDistance: Double?,
    plan: DayPlan?,
    modifier: Modifier = Modifier,
    sections: @Composable ColumnScope.() -> Unit = {},
) {
    val spacing = AppTheme.spacing
    val attendance = state.state

    state.sheet?.let { kind ->
        ClockSheet(
            kind = kind,
            submitting = state.submitting,
            submitError = state.submitError,
            onSubmit = onSubmit,
            onDismiss = onDismissSheet,
            notice = state.selfScheduledId?.let { stringResource(Res.string.self_schedule_saved) },
            branch = attendance?.branch,
            distance = previewDistance,
            locating = state.locating,
            located = state.preview != null || !state.locating,
            onRelocate = onRelocate,
        )
    }
    state.celebration?.let { ClockCelebrationOverlay(it, onFinishCelebration) }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        Column(modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight()) {
            LazyColumn(
                modifier = Modifier.weight(1f),
                contentPadding = PaddingValues(
                    horizontal = AppTheme.windowSize.pagePadding,
                    vertical = spacing.lg,
                ),
            ) {
                when {
                    state.loading -> item { LoadingState() }

                    state.failure != null || attendance == null -> item {
                        FailureState(failure = state.failure ?: AppFailure.Unexpected("Data kosong", "status"), onRetry = onRetry)
                    }

                    else -> {
                        if (attendance.notices.isNotEmpty()) {
                            item { AutoCloseNotices(attendance.notices, state.acknowledging, onAcknowledge) }
                        }

                        item {
                            PhasePanel(
                                segments = plan?.segments.orEmpty(),
                                clockedIn = attendance.record?.let { it.clockIn != null && it.clockOut == null } == true,
                            )
                        }

                        item { SectionTitle(stringResource(Res.string.attendance_today_schedule)) }
                        item { ScheduleCard(attendance.schedule) }

                        item { Box(modifier = Modifier.padding(top = spacing.md)) { StatusCard(attendance.record) } }

                        item {
                            ClockAction(
                                state = attendance,
                                onClock = onClock,
                                onSelfSchedule = onSelfSchedule,
                                modifier = Modifier.padding(top = spacing.md),
                            )
                        }

                        item {
                            PhotoPair(
                                first = PhotoItem(
                                    attendance.record?.photoInUrl,
                                    stringResource(Res.string.attendance_detail_photo_in),
                                ),
                                second = PhotoItem(
                                    attendance.record?.photoOutUrl,
                                    stringResource(Res.string.attendance_detail_photo_out),
                                ),
                                modifier = Modifier.padding(top = spacing.xl),
                            )
                        }
                    }
                }

                item { Column(modifier = Modifier.fillMaxWidth(), content = sections) }
            }
        }
    }
}

/** Tombol absen tepat di bawah kartu status: datang warna teks, pulang warna aksen, supaya keduanya tidak tertukar dan beda dari Pindai QR. */
@Composable
private fun ClockAction(
    state: AttendanceState,
    onClock: (ClockKind) -> Unit,
    onSelfSchedule: () -> Unit,
    modifier: Modifier = Modifier,
) {
    when {
        state.canClockOut -> PrimaryButton(
            text = stringResource(Res.string.attendance_action_out),
            onClick = { onClock(ClockKind.Out) },
            modifier = modifier,
        )
        state.canClockIn -> PrimaryButton(
            text = stringResource(Res.string.attendance_action_in),
            onClick = { onClock(ClockKind.In) },
            modifier = modifier,
        )
        // Tanpa jadwal hari ini, absen datang tetap tersedia dan dimulai dengan absen mandiri.
        state.canSelfSchedule -> PrimaryButton(
            text = stringResource(Res.string.attendance_action_in),
            onClick = onSelfSchedule,
            modifier = modifier,
        )
        else -> Notice(blockText(state.clockInBlock), modifier = modifier)
    }
}

/** Kalimat alasan absen datang terhalang, menyebut jadwal dan jamnya bila ada. */
@Composable
private fun blockText(block: ClockInBlock?): String {
    val schedule = block?.schedule?.let { scheduleLabel(it) }.orEmpty()
    val at = block?.at?.let { whenLabel(it) }.orEmpty()
    return when (block?.reason) {
        ClockInBlockReason.NotOpenYet -> stringResource(Res.string.attendance_block_not_open_yet, schedule, at)
        ClockInBlockReason.AlreadyUsed -> stringResource(Res.string.attendance_block_already_used, schedule)
        ClockInBlockReason.Ended -> stringResource(Res.string.attendance_block_ended, schedule, at)
        ClockInBlockReason.NoPermission -> stringResource(Res.string.attendance_block_no_permission)
        ClockInBlockReason.NoSchedule, null -> stringResource(Res.string.attendance_block_no_schedule)
    }
}

/** Kode shift bila ada, selain itu rentang jamnya. */
@Composable
private fun scheduleLabel(schedule: ScheduleSummary): String = schedule.code ?: timeRange(schedule)

@Composable
private fun timeRange(schedule: ScheduleSummary): String {
    val start = schedule.startsAt?.time
    val end = schedule.endsAt?.time
    return if (start != null && end != null) stringResource(Res.string.format_time_range, start, end) else ""
}

@Composable
private fun ScheduleCard(schedule: ScheduleSummary?) {
    ListCard {
        if (schedule == null) {
            Notice(stringResource(Res.string.attendance_no_schedule))
        } else {
            ShiftRow(
                title = timeRange(schedule),
                code = schedule.code,
                codeColor = parseHexColor(schedule.colorHex),
            )
        }
    }
}

@Composable
private fun StatusCard(record: AttendanceRecord?) {
    val (label, tone) = when {
        record?.clockOut != null -> stringResource(Res.string.attendance_status_out) to BadgeTone.Positive
        record?.clockIn != null -> stringResource(Res.string.attendance_status_in) to BadgeTone.Positive
        else -> stringResource(Res.string.attendance_status_none) to BadgeTone.Neutral
    }

    ListCard {
        DetailRow(
            stringResource(Res.string.attendance_detail_status),
            valueContent = {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
                ) {
                    StatusBadge(text = label, tone = tone)
                    if (record?.late == true) {
                        StatusBadge(text = stringResource(Res.string.attendance_late_badge), tone = BadgeTone.Warning)
                    }
                }
            },
        )
        AppDivider()
        DetailRow(
            stringResource(Res.string.attendance_clock_in),
            value = record?.clockIn?.let { whenLabel(it) } ?: NO_VALUE,
        )
        AppDivider()
        DetailRow(
            stringResource(Res.string.attendance_clock_out),
            valueContent = {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
                ) {
                    AppText(
                        text = record?.clockOut?.let { whenLabel(it) } ?: NO_VALUE,
                        role = TextRole.Body,
                        color = AppTheme.colors.content,
                    )
                    if (record?.autoClosed == true) {
                        StatusBadge(
                            text = stringResource(Res.string.attendance_detail_auto_closed),
                            tone = BadgeTone.Warning,
                        )
                    }
                }
            },
        )
    }
}
