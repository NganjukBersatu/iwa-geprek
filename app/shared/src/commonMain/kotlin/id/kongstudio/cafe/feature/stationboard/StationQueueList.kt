package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.station_correction_added
import id.kongstudio.cafe.resources.station_correction_changed
import id.kongstudio.cafe.resources.station_empty
import id.kongstudio.cafe.resources.station_empty_hint
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.resources.station_left_behind_from
import id.kongstudio.cafe.resources.station_locked_by
import id.kongstudio.cafe.resources.station_locked_hint
import id.kongstudio.cafe.resources.station_section_locked
import id.kongstudio.cafe.resources.station_section_started
import id.kongstudio.cafe.resources.station_section_stop
import id.kongstudio.cafe.resources.station_section_waiting
import id.kongstudio.cafe.resources.station_working_empty
import id.kongstudio.cafe.resources.station_working_empty_hint
import id.kongstudio.cafe.resources.station_stage_deliver
import id.kongstudio.cafe.resources.station_stage_handover
import id.kongstudio.cafe.resources.station_stage_make
import id.kongstudio.cafe.resources.station_started_by
import id.kongstudio.cafe.resources.station_stop_ok
import id.kongstudio.cafe.resources.station_stop_removed
import id.kongstudio.cafe.resources.station_stop_voided
import id.kongstudio.cafe.resources.station_timer_late
import id.kongstudio.cafe.resources.station_timer_remaining
import id.kongstudio.cafe.resources.station_timer_waiting
import id.kongstudio.cafe.resources.station_timer_working
import id.kongstudio.cafe.resources.station_waiting_rest
import id.kongstudio.cafe.resources.station_table
import id.kongstudio.cafe.resources.station_take_away
import id.kongstudio.cafe.resources.station_withdraw
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.boardcard.BoardCard
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.worktimer.TimerPhase
import id.kongstudio.cafe.ui.component.worktimer.WorkTimer
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

// Antrean atau Proses satu stasiun; yang harus dihentikan dan yang terkunci pembatalan tampil di keduanya karena mendesak.
@Composable
internal fun StationQueueList(
    station: Station,
    queue: StationQueue,
    working: Boolean,
    labels: DestinationLabels,
    enabled: Boolean,
    canWithdraw: (PendingCancellation) -> Boolean,
    onOpen: (QueueGroup) -> Unit,
    onClear: (taskIds: List<String>) -> Unit,
    onWithdraw: (requestId: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val groups = if (working) queue.started else queue.waiting
    if (queue.alerts.isEmpty() && queue.locked.isEmpty() && groups.isEmpty()) {
        Notice(
            text = stringResource(if (working) Res.string.station_working_empty else Res.string.station_empty),
            hint = stringResource(if (working) Res.string.station_working_empty_hint else Res.string.station_empty_hint),
            icon = when (station.kind) {
                StationKind.Make -> AppIcons.KitchenTools
                StationKind.Deliver -> AppIcons.Armchair
                StationKind.Handover -> AppIcons.Receipt
            },
            modifier = modifier,
        )
        return
    }
    val spacing = AppTheme.spacing
    val stopTitle = stringResource(Res.string.station_section_stop)
    val lockedTitle = stringResource(Res.string.station_section_locked)
    // Judul bagian hanya perlu bila ada bagian lain di atasnya; nama tab sudah menyebut isinya.
    val groupsTitle = stringResource(if (working) Res.string.station_section_started else Res.string.station_section_waiting)
    val needsTitle = queue.alerts.isNotEmpty() || queue.locked.isNotEmpty()

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = spacing.lg),
        verticalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        if (queue.alerts.isNotEmpty()) {
            item(key = "title-stop") { SectionTitle(stopTitle) }
            items(queue.alerts, key = { it.key }) { alert -> StopRow(alert, labels, enabled, onClear) }
        }
        if (queue.locked.isNotEmpty()) {
            item(key = "title-locked") { SectionTitle(lockedTitle) }
            items(queue.locked, key = { "locked:${it.order.id}" }) { locked -> LockedRow(locked, labels, enabled, canWithdraw, onWithdraw) }
        }
        if (groups.isNotEmpty()) {
            if (needsTitle) item(key = "title-groups") { SectionTitle(groupsTitle) }
            items(groups, key = { it.key }) { group -> GroupRow(station, group, labels, onOpen) }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun GroupRow(station: Station, group: QueueGroup, labels: DestinationLabels, onOpen: (QueueGroup) -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val stageLabel = stringResource(
        when (station.kind) {
            StationKind.Make -> Res.string.station_stage_make
            StationKind.Deliver -> Res.string.station_stage_deliver
            StationKind.Handover -> Res.string.station_stage_handover
        },
    )
    val timerLabels = timerLabels(group.stage)
    val startedBy = group.portions.firstNotNullOfOrNull { it.task.startedBy }
    val startedByText = startedBy?.let { stringResource(Res.string.station_started_by, it) }
    val restText = if (group.notArrived > 0) stringResource(Res.string.station_waiting_rest, group.notArrived) else null
    val correction = group.correction?.let {
        stringResource(if (it == Correction.Added) Res.string.station_correction_added else Res.string.station_correction_changed)
    }
    val destinations = if (station.kind == StationKind.Make) {
        group.portions.groupBy { it.order.id }.values.joinToString(" · ") { portions ->
            "${labels.of(portions.first().order)} (${portions.sumOf { it.line.quantity }})"
        }
    } else {
        null
    }

    BoardCard(
        modifier = Modifier.clip(AppTheme.shapes.field).clickable { onOpen(group) },
        container = colors.surface,
        gap = spacing.xs,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.widthIn(min = spacing.touchTarget), horizontalAlignment = Alignment.CenterHorizontally) {
                AppText(text = "${group.units}x", role = TextRole.Headline, color = colors.content)
            }
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
                AppText(text = group.title, role = TextRole.Title, color = colors.content)
                group.detail?.let { AppText(text = it, role = TextRole.Caption, color = colors.warning) }
                destinations?.let { AppText(text = it, role = TextRole.Caption, color = colors.contentMuted) }
                if (group.sessionCashiers.isNotEmpty() && group.leftBehind) {
                    AppText(text = stringResource(Res.string.station_left_behind_from, group.sessionCashiers.joinToString(", ")), role = TextRole.Caption, color = colors.danger)
                }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(spacing.xs), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
                    if (group.leftBehind) LeftBehindPill()
                    if (group.stage == Stage.Started) StatusBadge(stageLabel, BadgeTone.Accent)
                    correction?.let { StatusBadge(it, BadgeTone.Warning) }
                    restText?.let { StatusBadge(it, BadgeTone.Neutral) }
                    startedByText?.let { StatusBadge(it, BadgeTone.Neutral) }
                }
            }
            WorkTimer(sinceEpoch = group.sinceEpoch, targetSeconds = group.targetSeconds, labels = timerLabels)
        }
    }
}

@Composable
private fun StopRow(alert: StopAlert, labels: DestinationLabels, enabled: Boolean, onClear: (List<String>) -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(AppTheme.shapes.field)
            .background(colors.dangerContainer)
            .padding(spacing.md),
        verticalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        AppText(text = labels.of(alert.order), role = TextRole.Title, color = colors.onDangerContainer)
        AppText(text = alert.labels.joinToString(", "), role = TextRole.Body, color = colors.onDangerContainer)
        AppText(
            text = stringResource(if (alert.voided) Res.string.station_stop_voided else Res.string.station_stop_removed),
            role = TextRole.Label,
            color = colors.danger,
        )
        PrimaryButton(
            text = stringResource(Res.string.station_stop_ok),
            onClick = { onClear(alert.taskIds) },
            enabled = enabled,
            containerColor = colors.danger,
        )
    }
}

@Composable
private fun LockedRow(locked: LockedOrder, labels: DestinationLabels, enabled: Boolean, canWithdraw: (PendingCancellation) -> Boolean, onWithdraw: (String) -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val request = locked.order.cancellation ?: return
    BoardCard(container = colors.surface, gap = spacing.xs) {
        Row(horizontalArrangement = Arrangement.spacedBy(spacing.md), verticalAlignment = Alignment.CenterVertically) {
            IconBadge(AppIcons.Lock)
            Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
                AppText(text = labels.of(locked.order), role = TextRole.Title, color = colors.content)
                AppText(text = locked.portions.joinToString(", ") { lineLabel(it.line) }, role = TextRole.Body, color = colors.contentMuted)
                AppText(text = stringResource(Res.string.station_locked_by, request.requestedBy), role = TextRole.Caption, color = colors.contentMuted)
                AppText(text = stringResource(Res.string.station_locked_hint), role = TextRole.Caption, color = colors.danger)
            }
        }
        if (canWithdraw(request)) {
            SecondaryButton(text = stringResource(Res.string.station_withdraw), onClick = { onWithdraw(request.id) }, tone = ButtonTone.Cancel, enabled = enabled)
        }
    }
}

@Composable
internal fun timerLabels(stage: Stage): (TimerPhase) -> String {
    val waiting = stringResource(Res.string.station_timer_waiting)
    val working = stringResource(Res.string.station_timer_working)
    val remaining = stringResource(Res.string.station_timer_remaining)
    val late = stringResource(Res.string.station_timer_late)
    return { phase ->
        when (phase) {
            TimerPhase.Late -> late
            TimerPhase.Remaining -> remaining
            TimerPhase.Counting -> if (stage == Stage.Started) working else waiting
        }
    }
}

// Pembuat kata tujuan untuk layar ini; pola meja diambil sekali dari teks layar.
@Composable
internal fun rememberDestinationLabels(): DestinationLabels {
    val pattern = stringResource(Res.string.station_table, TablePlaceholder)
    val takeAway = stringResource(Res.string.station_take_away)
    return androidx.compose.runtime.remember(pattern, takeAway) { DestinationLabels({ pattern.replace(TablePlaceholder, it) }, takeAway) }
}

private const val TablePlaceholder = " "
