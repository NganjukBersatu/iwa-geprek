package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.resources.receipt_customer
import id.kongstudio.cafe.resources.station_history_delivered
import id.kongstudio.cafe.resources.station_history_delivering
import id.kongstudio.cafe.resources.station_history_destination
import id.kongstudio.cafe.resources.station_history_done
import id.kongstudio.cafe.resources.station_history_done_at
import id.kongstudio.cafe.resources.station_finished_empty
import id.kongstudio.cafe.resources.station_history_empty
import id.kongstudio.cafe.resources.station_history_finished
import id.kongstudio.cafe.resources.station_history_finished_at
import id.kongstudio.cafe.resources.station_history_handed
import id.kongstudio.cafe.resources.station_history_journey
import id.kongstudio.cafe.resources.station_history_journey_hint
import id.kongstudio.cafe.resources.station_history_line_note
import id.kongstudio.cafe.resources.station_history_made_by
import id.kongstudio.cafe.resources.station_history_not_arrived
import id.kongstudio.cafe.resources.station_history_not_delivered
import id.kongstudio.cafe.resources.station_history_not_printed
import id.kongstudio.cafe.resources.station_history_options
import id.kongstudio.cafe.resources.station_history_printed_at
import id.kongstudio.cafe.resources.station_history_reprint
import id.kongstudio.cafe.resources.station_history_system
import id.kongstudio.cafe.resources.station_history_this_menu
import id.kongstudio.cafe.resources.station_history_voided
import id.kongstudio.cafe.resources.station_history_waiting
import id.kongstudio.cafe.resources.station_history_working
import id.kongstudio.cafe.resources.station_kasir_detail_plain
import id.kongstudio.cafe.resources.station_kasir_detail_title
import id.kongstudio.cafe.resources.station_kasir_more
import id.kongstudio.cafe.resources.station_kasir_reprint_done
import id.kongstudio.cafe.resources.station_kasir_reprint_failed
import id.kongstudio.cafe.resources.station_kasir_reprint_no_printer
import id.kongstudio.cafe.resources.station_kasir_time
import id.kongstudio.cafe.resources.station_left_behind
import id.kongstudio.cafe.resources.station_left_behind_from
import id.kongstudio.cafe.resources.station_left_behind_later
import id.kongstudio.cafe.resources.station_left_behind_now
import id.kongstudio.cafe.resources.station_stage_handover
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconpill.IconPill
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.HeaderWidth
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.delay
import org.jetbrains.compose.resources.stringResource

private const val MinuteMillis = 30_000L
private const val SecondsPerMinute = 60

/** Keadaan satu menu di satu stasiun, dengan nada lencana yang sudah ada. */
internal class TaskStatus(val text: String, val tone: BadgeTone) {
    // Ikon membedakan keadaan tanpa bergantung pada warna lencana saja.
    val icon: ImageVector
        get() = when (tone) {
            BadgeTone.Positive -> AppIcons.Check
            BadgeTone.Accent -> AppIcons.Refresh
            BadgeTone.Warning -> AppIcons.Alert
            BadgeTone.Danger -> AppIcons.Close
            // Nada pekat bukan keadaan stasiun, jadi diperlakukan seperti netral.
            BadgeTone.Neutral, BadgeTone.Strong -> AppIcons.Clock
        }
}

@Composable
private fun TaskStatusBadge(status: TaskStatus) = StatusBadge(text = status.text, tone = status.tone, icon = status.icon)

/** Selesai atau Riwayat satu stasiun (menurut [HistoryState.part]): menu yang sudah selesai beserta keadaan terakhirnya, terbaru dulu. */
@Composable
internal fun StationHistoryList(
    station: Station,
    history: HistoryState,
    kinds: Map<String, StationKind>,
    labels: DestinationLabels,
    onOpen: (HistoryEntry) -> Unit,
    onMore: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val now = rememberMinuteNow()
    Loadable(loading = history.loading, modifier = modifier.fillMaxWidth()) {
        when {
            history.failure != null && history.entries.isEmpty() -> FailureState(failure = history.failure, onRetry = onRetry)
            history.entries.isEmpty() -> Notice(
                text = stringResource(if (history.part == HistoryPart.Moving) Res.string.station_finished_empty else Res.string.station_history_empty),
                icon = if (history.part == HistoryPart.Moving) AppIcons.Check else AppIcons.History,
            )
            else -> LazyColumn(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(spacing.md)) {
                item {
                    ListCard {
                        DividedItems(history.entries) { entry ->
                            val line = entry.line
                            val task = entry.task
                            val finished = task?.finishedEpoch?.let { stringResource(Res.string.station_history_finished, clockOf(it)) }
                            val status = entryStatus(entry, station, kinds, now)
                            ListRow(
                                title = line?.let(::lineLabel).orEmpty(),
                                detail = line?.let { (it.options + listOfNotNull(it.note)).joinToString(" · ").ifBlank { null } },
                                caption = listOfNotNull(labels.of(entry.order), labels.receiptBeside(entry.order), finished).joinToString(" · "),
                                trailing = { TaskStatusBadge(status) },
                                onClick = { onOpen(entry) },
                                opensDetail = true,
                            )
                        }
                    }
                }
                if (history.nextCursor != null) {
                    item {
                        Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                            history.moreFailure?.let { InlineMessage(text = failureText(it)) }
                            SecondaryButton(text = stringResource(Res.string.station_kasir_more), onClick = onMore, loading = history.loadingMore, modifier = Modifier.fillMaxWidth())
                        }
                    }
                }
                item { Column(modifier = Modifier.padding(bottom = spacing.lg)) {} }
            }
        }
    }
}

/** Halaman rincian satu menu Selesai atau Riwayat: menu ini dan cetak ulang, lalu perjalanan seluruh pesanan di bawahnya. */
@Composable
internal fun StationHistoryDetail(
    entry: HistoryEntry,
    station: Station,
    stations: List<Station>,
    labels: DestinationLabels,
    reprinting: Boolean,
    reprint: ReprintResult?,
    onReprint: () -> Unit,
    backLabel: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val now = rememberMinuteNow()
    val kinds = remember(stations) { stations.associate { it.id to it.kind } }
    val names = remember(stations) { stations.associate { it.id to it.name } }
    val order = entry.order
    val line = entry.line
    val task = entry.task
    val title = stringResource(Res.string.station_kasir_detail_title, order.receipt).takeIf { order.receipt.isNotBlank() }
        ?: stringResource(Res.string.station_kasir_detail_plain)

    val menu: @Composable () -> Unit = {
        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            AppText(text = stringResource(Res.string.station_history_this_menu), role = TextRole.Title)
            ListCard {
                line?.let { ListRow(title = lineLabel(it), trailing = { TaskStatusBadge(entryStatus(entry, station, kinds, now)) }) }
                DividedItems(
                    listOfNotNull(
                        stringResource(Res.string.station_history_destination) to labels.of(order),
                        line?.options?.takeIf { it.isNotEmpty() }?.let { stringResource(Res.string.station_history_options) to it.joinToString(", ") },
                        line?.note?.takeIf { it.isNotBlank() }?.let { stringResource(Res.string.station_history_line_note) to it },
                        task?.startedBy?.let { stringResource(Res.string.station_history_made_by) to it },
                        task?.finishedEpoch?.let { at ->
                            stringResource(Res.string.station_history_finished_at) to
                                (task.finishedBy?.let { "${clockOf(at)} · $it" } ?: stringResource(Res.string.station_history_system))
                        },
                        stringResource(Res.string.station_history_printed_at) to
                            (task?.printedEpoch?.let(::clockOf) ?: stringResource(Res.string.station_history_not_printed)),
                        order.customerName?.let { stringResource(Res.string.receipt_customer) to it },
                        stringResource(Res.string.station_kasir_time) to whenLabel(DateTimeFormat.stampAt(order.createdEpoch)),
                    ),
                ) { (label, value) -> DetailRow(label = label, value = value) }
            }
            PrimaryButton(text = stringResource(Res.string.station_history_reprint), onClick = onReprint, loading = reprinting, enabled = !reprinting)
            reprint?.let { result ->
                val printer = station.name
                when (result) {
                    ReprintResult.Printed -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_done, printer), tone = MessageTone.Success)
                    ReprintResult.NoPrinter -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_no_printer, printer))
                    ReprintResult.Failed -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_failed, printer))
                }
            }
        }
    }
    val journey: @Composable () -> Unit = {
        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            AppText(text = stringResource(Res.string.station_history_journey), role = TextRole.Title)
            ListCard {
                val steps = order.lines.flatMap { orderLine -> orderLine.tasks.map { orderLine to it } }
                DividedItems(steps) { (orderLine, step) ->
                    val status = taskStatus(order, step, kinds[step.stationId] ?: StationKind.Make, now)
                    ListRow(
                        title = lineLabel(orderLine),
                        caption = names[step.stationId],
                        trailing = { TaskStatusBadge(status) },
                    )
                }
            }
            AppText(text = stringResource(Res.string.station_history_journey_hint), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        }
    }

    PlatformBackHandler(enabled = true, onBack = onBack)
    Column(modifier = modifier.fillMaxSize()) {
        SubPageHeader(
            title = title,
            back = HeaderBack(backLabel, onBack),
            width = HeaderWidth.Page,
            trailing = { TaskStatusBadge(entryStatus(entry, station, kinds, now)) },
        )
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(AppTheme.windowSize.pagePadding),
            verticalArrangement = Arrangement.spacedBy(spacing.lg),
        ) {
            menu()
            journey()
        }
    }
}

/** Lencana merah Tertinggal: sesi kasir pesanannya sudah ditutup, sedangkan menunya belum selesai. */
@Composable
internal fun LeftBehindPill(modifier: Modifier = Modifier) {
    IconPill(
        icon = AppIcons.Alert,
        text = stringResource(Res.string.station_left_behind),
        modifier = modifier,
        containerColor = AppTheme.colors.dangerContainer,
        contentColor = AppTheme.colors.onDangerContainer,
    )
}

/** Satu baris dalam modal Tertinggal; [cashier] kasir sesi asal pesanan. */
internal class LeftBehindRow(val key: String, val title: String, val detail: String, val cashier: String?)

/** Modal pengingat Tertinggal; Nanti hanya menutup, dan modal muncul lagi di pembukaan berikutnya selama masih ada. */
@Composable
internal fun LeftBehindDialog(title: String, body: String, rows: List<LeftBehindRow>, onNow: () -> Unit, onLater: () -> Unit) {
    val spacing = AppTheme.spacing
    AppDialog(title = title, onDismiss = onLater) {
        Column(
            modifier = Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(spacing.lg),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            LeftBehindPill()
            AppText(text = body, role = TextRole.Body, color = AppTheme.colors.contentMuted)
            ListCard {
                DividedItems(rows) { row ->
                    val from = row.cashier?.let { stringResource(Res.string.station_left_behind_from, it) }
                    ListRow(title = row.title, caption = listOfNotNull(row.detail, from).joinToString(" · "))
                }
            }
            PrimaryButton(text = stringResource(Res.string.station_left_behind_now), onClick = onNow)
            SecondaryButton(text = stringResource(Res.string.station_left_behind_later), onClick = onLater, tone = ButtonTone.Cancel)
        }
    }
}

// Keadaan terakhir menu Riwayat: di stasiun pembuat yang dilihat langkah pengantarnya, selain itu langkah stasiun ini sendiri.
@Composable
private fun entryStatus(entry: HistoryEntry, station: Station, kinds: Map<String, StationKind>, now: Long): TaskStatus {
    val own = entry.task
    val next = entry.line?.tasks?.firstOrNull { (kinds[it.stationId] ?: StationKind.Make) != StationKind.Make }
    if (station.kind == StationKind.Make && next != null) {
        return taskStatus(entry.order, next, kinds[next.stationId] ?: StationKind.Deliver, now, own?.finishedEpoch)
    }
    if (own == null) return TaskStatus(stringResource(Res.string.station_history_done), BadgeTone.Positive)
    return taskStatus(entry.order, own, station.kind, now)
}

@Composable
private fun taskStatus(order: BoardOrder, task: BoardTask, kind: StationKind, now: Long, readySince: Long? = null): TaskStatus {
    val finishedAt = task.finishedEpoch
    return when {
        order.voided || task.removed -> TaskStatus(stringResource(Res.string.station_history_voided), BadgeTone.Danger)
        finishedAt != null && task.finishedBy == null -> TaskStatus(stringResource(Res.string.station_history_system), BadgeTone.Neutral)
        finishedAt != null -> {
            val who = task.finishedBy.orEmpty()
            val text = when (kind) {
                StationKind.Make -> stringResource(Res.string.station_history_done_at, clockOf(finishedAt), who)
                StationKind.Deliver -> stringResource(Res.string.station_history_delivered, clockOf(finishedAt), who)
                StationKind.Handover -> stringResource(Res.string.station_history_handed, clockOf(finishedAt), who)
            }
            TaskStatus(text, BadgeTone.Positive)
        }
        task.stage == Stage.Started -> when (kind) {
            StationKind.Make -> TaskStatus(stringResource(Res.string.station_history_working, task.startedBy.orEmpty()), BadgeTone.Accent)
            StationKind.Deliver -> TaskStatus(stringResource(Res.string.station_history_delivering), BadgeTone.Accent)
            StationKind.Handover -> TaskStatus(stringResource(Res.string.station_stage_handover), BadgeTone.Accent)
        }
        kind == StationKind.Make && task.arrivedEpoch != null -> TaskStatus(stringResource(Res.string.station_history_waiting), BadgeTone.Neutral)
        kind == StationKind.Make -> TaskStatus(stringResource(Res.string.station_history_not_arrived), BadgeTone.Neutral)
        else -> {
            val since = task.arrivedEpoch ?: readySince
            if (since == null) {
                TaskStatus(stringResource(Res.string.station_history_not_arrived), BadgeTone.Neutral)
            } else {
                val minutes = ((now - since) / SecondsPerMinute).coerceAtLeast(0).toInt()
                TaskStatus(stringResource(Res.string.station_history_not_delivered, minutes), BadgeTone.Warning)
            }
        }
    }
}

private fun clockOf(epoch: Long): String = DateTimeFormat.stampAt(epoch).time

// Jam tablet yang diperbarui berkala supaya lama "Belum diantar" ikut berjalan tanpa memuat ulang data.
@Composable
private fun rememberMinuteNow(): Long {
    var now by remember { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(MinuteMillis)
            now = ServerClock.nowEpochSeconds()
        }
    }
    return now
}
