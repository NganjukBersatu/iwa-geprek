package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.resources.station_unmute
import id.kongstudio.cafe.resources.station_muted_left
import id.kongstudio.cafe.resources.station_mute_five
import id.kongstudio.cafe.core.time.ServerClock
import kotlinx.coroutines.delay
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.sound.AppSound
import id.kongstudio.cafe.core.sound.rememberSoundPlayer
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.printer.PrintOutcome
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_close
import id.kongstudio.cafe.resources.nav_stations
import id.kongstudio.cafe.resources.station_connected
import id.kongstudio.cafe.resources.station_kasir_no_session
import id.kongstudio.cafe.resources.station_left_behind_body
import id.kongstudio.cafe.resources.station_left_behind_title
import id.kongstudio.cafe.resources.station_none_held
import id.kongstudio.cafe.resources.station_notice_approved
import id.kongstudio.cafe.resources.station_notice_note
import id.kongstudio.cafe.resources.station_notice_rejected
import id.kongstudio.cafe.resources.station_offline_locked
import id.kongstudio.cafe.resources.station_reconnecting
import id.kongstudio.cafe.resources.station_slip_failed
import id.kongstudio.cafe.resources.station_slip_reprint
import id.kongstudio.cafe.resources.station_slip_unpaired
import id.kongstudio.cafe.resources.station_sound_toggle
import id.kongstudio.cafe.resources.station_tab_count
import id.kongstudio.cafe.resources.station_truncated
import id.kongstudio.cafe.resources.station_view_history
import id.kongstudio.cafe.resources.station_view_working
import id.kongstudio.cafe.resources.station_view_finished
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.station_view_queue
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.loadable.LoadingVariant
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

// Papan stasiun yang ditetapkan untuk tablet ini: satu tab per stasiun, antrean kerja, lalu halaman kerja satu kelompok saat diketuk.
/** Batas pesan gangguan per halaman; sisanya muncul setelah yang tampil ditutup. */
private const val MaxBoardBanners = 5

@Composable
internal fun StationBoardScreen(
    viewModel: StationBoardViewModel,
    access: UserAccess,
    cashierOrders: CashierOrdersViewModel?,
    modifier: Modifier = Modifier,
    focusHandover: Boolean = false,
    onFocusHandled: () -> Unit = {},
) {
    val state by viewModel.state.collectAsState()
    // Permintaan membuka tab Kasir dipenuhi begitu stasiun tablet ini terbaca.
    LaunchedEffect(focusHandover, state.held) {
        if (!focusHandover || state.loading) return@LaunchedEffect
        state.held.firstOrNull { it.kind == StationKind.Handover }?.let { viewModel.select(it.id) }
        onFocusHandled()
    }
    val role = state.active
    val labels = rememberDestinationLabels()
    val enabled = state.connected && !state.stepping
    val queue = remember(role, state.orders, labels) { role?.let { queueOf(it, state.orders, labels) } }
    // Pengajuan orang lain hanya boleh ditarik oleh yang berhak memutuskannya; server tetap yang menolak.
    val canWithdraw: (PendingCancellation) -> Boolean = { canWithdrawCancel(access, it.requestedById) }

    val open = state.openTaskIds
    // Antrean menunggu tiap stasiun yang dipegang, untuk angka di tab dan bunyi menu baru walaupun tab lain yang terbuka.
    val waiting = remember(state.stations, state.orders, labels) {
        state.held.filter { it.kind != StationKind.Handover }.associate { station ->
            station.id to queueOf(station, state.orders, labels).waiting.flatMap { it.taskIds }.toSet()
        }
    }
    var mutedUntil by rememberSaveable { mutableLongStateOf(0L) }
    val soundOn = mutedUntil == 0L
    // Pengingat tiap stasiun yang bunyinya menyala: kapan menu tertunggu paling lama tiba dan berapa jeda ulangnya.
    val reminders = remember(state.stations, state.orders, labels, state.mutedIds) {
        state.held.filter { it.kind != StationKind.Handover && it.reminderSeconds > 0 && it.id !in state.mutedIds }.mapNotNull { station ->
            queueOf(station, state.orders, labels).waiting.minOfOrNull { it.sinceEpoch }?.let { Reminder(it, station.reminderSeconds) }
        }
    }
    ArrivalSound(
        enabled = soundOn,
        ready = !state.loading && state.failure == null,
        waitingIds = waiting.filterKeys { it !in state.mutedIds }.values.flatten().toSet(),
        reminders = reminders,
    )
    LaunchedEffect(mutedUntil) {
        if (mutedUntil == 0L) return@LaunchedEffect
        delay(((mutedUntil - ServerClock.nowEpochSeconds()).coerceAtLeast(0L) + 1L) * MillisPerSecond)
        mutedUntil = 0L
    }
    val detailPortions = remember(open, state.orders, role) {
        if (role == null || open.isEmpty()) emptyList()
        else state.orders.flatMap { order -> order.lines.mapNotNull { line -> line.taskAt(role.id)?.takeIf { it.id in open }?.let { Portion(order, line, it) } } }
    }
    // Bunyi berlaku untuk stasiun, bukan untuk Antrean atau Riwayat, jadi kendalinya di kepala papan dan tetap tampil di kedua tampilan.
    val soundBar: (@Composable () -> Unit)? = if (role != null && role.kind != StationKind.Handover) {
        {
            StationSoundBar(
                label = stringResource(Res.string.station_sound_toggle, role.name),
                checked = role.id !in state.mutedIds,
                onCheckedChange = { viewModel.toggleSound(role.id) },
                mutedUntil = mutedUntil,
                onMute = { mutedUntil = ServerClock.nowEpochSeconds() + MuteSeconds },
                onUnmute = { mutedUntil = 0L },
            )
        }
    } else {
        null
    }
    val wide = AppTheme.windowSize.isWide
    val header: @Composable () -> Unit = {
        Spacer(Modifier.height(AppTheme.spacing.lg))
        PageTitle(title = role?.name ?: stringResource(Res.string.nav_stations)) {
            if (wide) soundBar?.invoke()
            if (!state.loading && state.failure == null) {
                StatusBadge(
                    text = stringResource(if (state.connected) Res.string.station_connected else Res.string.station_reconnecting),
                    tone = if (state.connected) BadgeTone.Positive else BadgeTone.Warning,
                )
            }
        }
        if (!wide) soundBar?.invoke()
        if (state.held.size > 1) {
            StationTabs(stations = state.held, activeId = state.activeId, waiting = waiting, onSelect = viewModel::select)
        }
        if (role != null && role.kind != StationKind.Handover) {
            // Angka di Antrean dan Proses dihitung dari papan; Selesai dan Riwayat dibaca per halaman, jadi tanpa angka.
            val counts = queue?.let { mapOf(BoardView.Queue to it.waiting.sumOf { group -> group.units }, BoardView.Working to it.started.sumOf { group -> group.units }) }.orEmpty()
            val names = mapOf(
                BoardView.Queue to stringResource(Res.string.station_view_queue),
                BoardView.Working to stringResource(Res.string.station_view_working),
                BoardView.Finished to stringResource(Res.string.station_view_finished),
                BoardView.History to stringResource(Res.string.station_view_history),
            )
            SegmentedControl(
                options = BoardView.entries.map { view ->
                    val name = names.getValue(view)
                    val count = counts[view] ?: 0
                    if (count > 0) stringResource(Res.string.station_tab_count, name, count) else name
                },
                selectedIndex = state.view.ordinal,
                onSelect = { viewModel.showView(BoardView.entries[it]) },
                modifier = Modifier.padding(top = AppTheme.spacing.sm),
            )
        }
    }
    val swipe = Modifier.swipeTabs(state.held, state.activeId, viewModel::select)
    val openEntry = state.openEntry

    LeftBehindReminder(state = state, labels = labels, onHandle = { stationId ->
        viewModel.select(stationId)
        viewModel.showView(BoardView.Queue)
    })

    if (role?.kind == StationKind.Handover) {
        // Station Kasir tidak punya antrean kerja: checkpoint-nya terpenuhi saat pesanan dibayar.
        if (cashierOrders != null) {
            CashierOrdersScreen(
                viewModel = cashierOrders,
                canWithdraw = { canWithdrawCancel(access, it.requestedById) },
                listTitle = role.name,
                header = header,
                modifier = modifier.then(swipe),
            )
        } else {
            Column(modifier = modifier.fillMaxSize().then(swipe).padding(horizontal = AppTheme.windowSize.pagePadding)) {
                header()
                Spacer(Modifier.height(AppTheme.spacing.md))
                Notice(stringResource(Res.string.station_kasir_no_session))
            }
        }
    } else if (role != null && openEntry != null) {
        StationHistoryDetail(
            entry = openEntry,
            station = role,
            stations = state.stations,
            labels = labels,
            reprinting = state.reprinting,
            reprint = state.reprint,
            onReprint = viewModel::reprintEntry,
            backLabel = stringResource(
                Res.string.back_to_page,
                stringResource(if (state.view == BoardView.Finished) Res.string.station_view_finished else Res.string.station_view_history),
            ),
            onBack = viewModel::closeHistory,
            modifier = modifier,
        )
    } else if (role != null && detailPortions.isNotEmpty()) {
        StationDetail(
            station = role,
            portions = detailPortions,
            labels = labels,
            recipe = state.recipe,
            workers = state.workers,
            chosenWorkerId = role.let { state.workerChoice[it.id] },
            onChooseWorker = { workerId -> viewModel.chooseWorker(role.id, workerId) },
            enabled = enabled,
            stepping = state.stepping,
            failure = state.stepFailure,
            onStep = viewModel::step,
            // Kembali ke tab tempat menu ini dibuka, walaupun tahapnya sudah berpindah.
            backLabel = stringResource(
                Res.string.back_to_page,
                stringResource(if (state.view == BoardView.Working) Res.string.station_view_working else Res.string.station_view_queue),
            ),
            onClose = viewModel::close,
            modifier = modifier,
        )
    } else {
        Column(modifier = modifier.fillMaxSize().then(swipe).padding(horizontal = AppTheme.windowSize.pagePadding)) {
            header()
            Spacer(Modifier.height(AppTheme.spacing.md))
            val stationFailure = state.failure
            Loadable(loading = state.loading, variant = LoadingVariant.Board, modifier = Modifier.weight(1f).fillMaxWidth()) {
                when {
                    stationFailure != null -> FailureState(failure = stationFailure, onRetry = viewModel::reload)
                    role == null || queue == null -> Notice(stringResource(Res.string.station_none_held))
                    state.view.historyPart != null -> StationHistoryList(
                        station = role,
                        history = state.history,
                        kinds = state.stations.associate { it.id to it.kind },
                        labels = labels,
                        onOpen = viewModel::openHistory,
                        onMore = viewModel::loadMoreHistory,
                        onRetry = viewModel::retryHistory,
                        modifier = Modifier.fillMaxSize(),
                    )
                    else -> Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
                        if (!state.connected) StatusBanner(text = stringResource(Res.string.station_offline_locked), tone = BannerTone.Warning)
                        if (state.truncated) StatusBanner(text = stringResource(Res.string.station_truncated), tone = BannerTone.Warning)
                        val slipFailure = state.slipFailures[role.id]
                        val systemBanners = listOf(!state.connected, state.truncated, slipFailure != null, state.stepFailure != null).count { it }
                        state.notices.take((MaxBoardBanners - systemBanners).coerceAtLeast(1)).forEach { notice -> DecisionBanner(notice, onClose = { viewModel.dismissNotice(notice.requestId) }) }
                                                slipFailure?.let { failure ->
                            StatusBanner(
                                text = if (failure.outcome == PrintOutcome.NotPaired) {
                                    stringResource(Res.string.station_slip_unpaired, role.name, failure.slips.size)
                                } else {
                                    stringResource(Res.string.station_slip_failed, failure.slips.size)
                                },
                                tone = BannerTone.Warning,
                                actionLabel = stringResource(Res.string.station_slip_reprint),
                                onAction = { viewModel.reprintSlips(role.id) },
                            )
                        }
                        state.stepFailure?.let { failure ->
                            StatusBanner(
                                text = failureText(failure),
                                tone = BannerTone.Warning,
                                actionLabel = stringResource(Res.string.common_close),
                                onAction = viewModel::dismissStepFailure,
                            )
                        }
                        StationQueueList(
                            station = role,
                            queue = queue,
                            working = state.view == BoardView.Working,
                            labels = labels,
                            enabled = enabled,
                            canWithdraw = canWithdraw,
                            onOpen = viewModel::open,
                            onClear = { ids -> viewModel.step(StepKind.Clear, ids, Stage.Waiting) },
                            onWithdraw = viewModel::withdrawCancel,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun DecisionBanner(notice: DecisionNotice, onClose: () -> Unit) {
    val head = stringResource(if (notice.approved) Res.string.station_notice_approved else Res.string.station_notice_rejected, notice.receipt, notice.decidedBy)
    val note = notice.note?.takeIf { it.isNotBlank() }?.let { stringResource(Res.string.station_notice_note, it) }
    StatusBanner(
        text = listOfNotNull(head, note).joinToString(" "),
        tone = if (notice.approved) BannerTone.Info else BannerTone.Warning,
        actionLabel = stringResource(Res.string.common_close),
        onAction = onClose,
    )
}

// Waktu tiba menu yang paling lama menunggu di satu stasiun beserta jeda ulang bunyinya.
private class Reminder(val oldestEpoch: Long, val intervalSeconds: Int)

private const val MuteSeconds = 5L * 60L
private const val MillisPerSecond = 1_000L

// Bunyi alarm sekali setiap ada menu baru masuk antrean di Mode Stasiun, lalu pengingat berulang selama masih ada menu yang belum dimulai; menu yang sudah ada saat layar dibuka tidak berbunyi sebagai menu baru.
@Composable
private fun ArrivalSound(enabled: Boolean, ready: Boolean, waitingIds: Set<String>, reminders: List<Reminder>) {
    val sound = rememberSoundPlayer()
    val seen = remember { mutableSetOf<String>() }
    var primed by remember { mutableStateOf(false) }
    var lastRing by remember { mutableLongStateOf(0L) }
    LaunchedEffect(waitingIds, enabled, ready) {
        if (!ready) return@LaunchedEffect
        val fresh = waitingIds - seen
        seen += waitingIds
        if (primed && enabled && fresh.isNotEmpty()) {
            sound.play(AppSound.OrderArrived)
            lastRing = ServerClock.nowEpochSeconds()
        }
        primed = true
    }
    // Satu bunyi untuk seluruh papan: berbunyi bila ada stasiun yang menunya sudah menunggu selama jedanya, lalu menunggu jeda itu lagi.
    LaunchedEffect(enabled, ready, reminders) {
        if (!enabled || !ready || reminders.isEmpty()) return@LaunchedEffect
        while (true) {
            delay(MillisPerSecond)
            val now = ServerClock.nowEpochSeconds()
            val due = reminders.filter { now - it.oldestEpoch >= it.intervalSeconds }
            val interval = due.minOfOrNull { it.intervalSeconds } ?: continue
            if (now - lastRing >= interval) {
                sound.play(AppSound.OrderArrived)
                lastRing = now
            }
        }
    }
}

/** Tab stasiun yang dipegang tablet; angka menunjukkan menu yang menunggu di tab lain. */
@Composable
private fun StationTabs(stations: List<Station>, activeId: String?, waiting: Map<String, Set<String>>, onSelect: (String) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(top = AppTheme.spacing.sm),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        stations.forEach { station ->
            val count = waiting[station.id]?.size ?: 0
            AppChip(
                label = if (count > 0 && station.id != activeId) stringResource(Res.string.station_tab_count, station.name, count) else station.name,
                selected = station.id == activeId,
                onClick = { onSelect(station.id) },
            )
        }
    }
}

// Geser ke kiri membuka tab berikutnya, ke kanan tab sebelumnya; tablet dengan satu stasiun tidak terpengaruh.
private fun Modifier.swipeTabs(stations: List<Station>, activeId: String?, onSelect: (String) -> Unit): Modifier {
    if (stations.size < 2) return this
    return pointerInput(stations, activeId) {
        var dragged = 0f
        detectHorizontalDragGestures(
            onDragStart = { dragged = 0f },
            onHorizontalDrag = { _, amount -> dragged += amount },
            onDragEnd = {
                val index = stations.indexOfFirst { it.id == activeId }
                val threshold = size.width * SwipeFraction
                when {
                    dragged < -threshold && index < stations.lastIndex -> onSelect(stations[index + 1].id)
                    dragged > threshold && index > 0 -> onSelect(stations[index - 1].id)
                }
            },
        )
    }
}

private const val SwipeFraction = 0.2f

// Modal menu Tertinggal milik stasiun tablet ini; muncul saat papan dibuka atau ada yang baru tertinggal, dan Nanti hanya berlaku selama layar ini terbuka.
@Composable
private fun LeftBehindReminder(state: StationBoardState, labels: DestinationLabels, onHandle: (stationId: String) -> Unit) {
    var dismissed by remember { mutableStateOf(emptySet<String>()) }
    val rows = remember(state.held, state.orders, labels) {
        state.held.filter { it.kind != StationKind.Handover }.flatMap { station ->
            state.orders.filter { it.leftBehind && !it.voided && it.cancellation == null }.flatMap { order ->
                order.lines.mapNotNull { line ->
                    val task = line.taskAt(station.id)?.takeIf { !it.removed && it.arrivedEpoch != null && it.stage != Stage.Finished } ?: return@mapNotNull null
                    val detail = listOfNotNull(labels.receiptBeside(order), station.name).joinToString(" · ")
                    station.id to LeftBehindRow(key = task.id, title = "${lineLabel(line)} · ${labels.of(order)}", detail = detail, cashier = order.sessionCashier)
                }
            }
        }
    }
    val fresh = rows.filter { it.second.key !in dismissed }
    if (state.loading || state.failure != null || fresh.isEmpty()) return
    val all = rows.map { it.second.key }.toSet()
    LeftBehindDialog(
        title = stringResource(Res.string.station_left_behind_title, rows.size),
        body = stringResource(Res.string.station_left_behind_body),
        rows = rows.map { it.second },
        onNow = {
            dismissed = dismissed + all
            onHandle(fresh.first().first)
        },
        onLater = { dismissed = dismissed + all },
    )
}


