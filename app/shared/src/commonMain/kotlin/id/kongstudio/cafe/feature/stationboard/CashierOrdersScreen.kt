package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.feature.printer.printerSlotName
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.station_kasir_count
import id.kongstudio.cafe.resources.station_kasir_count_more
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.resources.cashier_line_note
import id.kongstudio.cafe.resources.cashier_total
import id.kongstudio.cafe.resources.order_voided
import id.kongstudio.cafe.resources.receipt_cashier
import id.kongstudio.cafe.resources.receipt_customer
import id.kongstudio.cafe.resources.station_cancel_request
import id.kongstudio.cafe.resources.station_kasir_cancel_hint
import id.kongstudio.cafe.resources.station_kasir_detail_plain
import id.kongstudio.cafe.resources.station_kasir_detail_title
import id.kongstudio.cafe.resources.station_kasir_dine_in
import id.kongstudio.cafe.resources.station_kasir_discount
import id.kongstudio.cafe.resources.station_kasir_done
import id.kongstudio.cafe.resources.station_kasir_empty
import id.kongstudio.cafe.resources.station_kasir_left_behind_banner
import id.kongstudio.cafe.resources.station_kasir_left_behind_section
import id.kongstudio.cafe.resources.station_kasir_more
import id.kongstudio.cafe.resources.station_kasir_no_match
import id.kongstudio.cafe.resources.station_kasir_note
import id.kongstudio.cafe.resources.station_kasir_payment
import id.kongstudio.cafe.resources.station_kasir_pending
import id.kongstudio.cafe.resources.station_kasir_reprint
import id.kongstudio.cafe.resources.station_kasir_reprint_station
import id.kongstudio.cafe.resources.station_kasir_reprint_done
import id.kongstudio.cafe.resources.station_kasir_reprint_failed
import id.kongstudio.cafe.resources.station_kasir_reprint_no_printer
import id.kongstudio.cafe.resources.station_kasir_running
import id.kongstudio.cafe.resources.station_kasir_search
import id.kongstudio.cafe.resources.station_kasir_table
import id.kongstudio.cafe.resources.station_kasir_this_session
import id.kongstudio.cafe.resources.station_kasir_time
import id.kongstudio.cafe.resources.station_kasir_type
import id.kongstudio.cafe.resources.station_left_behind_from
import id.kongstudio.cafe.resources.station_locked_by
import id.kongstudio.cafe.resources.station_take_away
import id.kongstudio.cafe.resources.station_withdraw
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.searchfield.SearchField
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.HeaderWidth
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Station Kasir: pesanan sesi aktif yang bisa dicari, dibuka rinciannya, dicetak ulang, dan diajukan batal. */
@Composable
internal fun CashierOrdersScreen(
    viewModel: CashierOrdersViewModel,
    canWithdraw: (CashierCancellation) -> Boolean,
    listTitle: String,
    header: @Composable () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val open = state.openOrder
    if (open != null) {
        CashierOrderDetail(order = open, state = state, viewModel = viewModel, canWithdraw = canWithdraw, listTitle = listTitle, modifier = modifier)
    } else {
        CashierOrderList(state = state, viewModel = viewModel, header = header, modifier = modifier)
    }

    if (open != null && state.askingCancel && open.pendingCancel == null) {
        CancelRequestSheet(
            receipt = open.receipt.orEmpty(),
            total = open.total,
            sending = state.cancelling,
            failure = state.cancelFailure,
            onSend = viewModel::requestCancel,
            onDismiss = viewModel::closeCancel,
        )
    }
}

@Composable
private fun CashierOrderList(state: CashierOrdersState, viewModel: CashierOrdersViewModel, header: @Composable () -> Unit, modifier: Modifier) {
    val spacing = AppTheme.spacing
    Column(modifier = modifier.fillMaxSize().padding(horizontal = AppTheme.windowSize.pagePadding), verticalArrangement = Arrangement.spacedBy(spacing.md)) {
        header()
        SearchField(value = state.query, onValueChange = viewModel::search, label = stringResource(Res.string.station_kasir_search), modifier = Modifier.fillMaxWidth())
        // Pesanan tertinggal dari sesi lain tampil paling atas selama tidak sedang mencari.
        val leftBehind = if (state.query.isBlank()) state.leftBehind else emptyList()
        if (state.query.isBlank()) state.leftBehindFailure?.let { InlineMessage(text = failureText(it)) }
        if (state.query.isBlank() && state.orders.isNotEmpty()) {
            // Daftar dimuat per halaman tanpa total dari server, jadi angka diberi tanda "+" selama masih ada halaman berikutnya.
            val count = stringResource(if (state.nextCursor == null) Res.string.station_kasir_count else Res.string.station_kasir_count_more, state.orders.size)
            AppText(text = count, role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        }
        Loadable(loading = state.loading, modifier = Modifier.weight(1f).fillMaxWidth()) {
            when {
                state.failure != null && state.orders.isEmpty() -> FailureState(failure = state.failure, onRetry = viewModel::retry)
                state.orders.isEmpty() && leftBehind.isEmpty() -> Notice(
                    text = if (state.query.isBlank()) stringResource(Res.string.station_kasir_empty) else stringResource(Res.string.station_kasir_no_match, state.query.trim()),
                )
                else -> LazyColumn(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(spacing.md)) {
                    if (leftBehind.isNotEmpty()) {
                        item { StatusBanner(text = stringResource(Res.string.station_kasir_left_behind_banner, leftBehind.size), tone = BannerTone.Warning) }
                        item { SectionTitle(stringResource(Res.string.station_kasir_left_behind_section)) }
                        item {
                            ListCard {
                                DividedItems(leftBehind) { order -> OrderRow(order = order, leftBehind = true, onOpen = { viewModel.open(order) }) }
                            }
                        }
                        if (state.orders.isNotEmpty()) item { SectionTitle(stringResource(Res.string.station_kasir_this_session)) }
                    }
                    if (state.orders.isNotEmpty()) {
                        item {
                            ListCard {
                                DividedItems(state.orders) { order -> OrderRow(order = order, onOpen = { viewModel.open(order) }) }
                            }
                        }
                    }
                    if (state.nextCursor != null) {
                        item {
                            Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                                state.moreFailure?.let { InlineMessage(text = failureText(it)) }
                                SecondaryButton(text = stringResource(Res.string.station_kasir_more), onClick = viewModel::loadMore, loading = state.loadingMore, modifier = Modifier.fillMaxWidth())
                            }
                        }
                    }
                    item { Column(modifier = Modifier.padding(bottom = spacing.lg)) {} }
                }
            }
        }
    }
}

@Composable
private fun OrderRow(order: CashierOrder, onOpen: () -> Unit, leftBehind: Boolean = false) {
    val time = DateTimeFormat.stampAt(isoToEpoch(order.createdAt) ?: 0L).time
    val items = order.lines.joinToString(", ") { "${it.quantity} ${it.name}" }
    val from = order.cashierName?.takeIf { leftBehind }?.let { stringResource(Res.string.station_left_behind_from, it) }
    ListRow(
        title = listOfNotNull(order.receipt?.let { "#$it" }, placeOf(order), order.customerName).joinToString(" · "),
        caption = listOfNotNull(time, items, order.paymentLabel, from).joinToString(" · "),
        badge = if (leftBehind) {
            { LeftBehindPill() }
        } else {
            null
        },
        leading = { IconBadge(icon = if (order.takeAway) AppIcons.ShoppingBag else AppIcons.Armchair) },
        trailing = {
            Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
                AppText(text = formatRupiah(order.total), role = TextRole.Title)
                StatusOf(order)
            }
        },
        onClick = onOpen,
        opensDetail = true,
    )
}

@Composable
private fun placeOf(order: CashierOrder): String =
    if (order.takeAway) stringResource(Res.string.station_take_away) else order.tableNo?.let { stringResource(Res.string.station_kasir_table, it) } ?: stringResource(Res.string.station_kasir_dine_in)

@Composable
private fun StatusOf(order: CashierOrder) {
    when {
        order.voided -> StatusBadge(text = stringResource(Res.string.order_voided), tone = BadgeTone.Danger, icon = AppIcons.Close)
        order.pendingCancel != null -> StatusBadge(text = stringResource(Res.string.station_kasir_pending), tone = BadgeTone.Warning, icon = AppIcons.Lock)
        order.served -> StatusBadge(text = stringResource(Res.string.station_kasir_done), tone = BadgeTone.Positive, icon = AppIcons.Check)
        else -> StatusBadge(text = stringResource(Res.string.station_kasir_running), tone = BadgeTone.Accent, icon = AppIcons.Clock)
    }
}

@Composable
private fun CashierOrderDetail(
    order: CashierOrder,
    state: CashierOrdersState,
    viewModel: CashierOrdersViewModel,
    canWithdraw: (CashierCancellation) -> Boolean,
    listTitle: String,
    modifier: Modifier,
) {
    val spacing = AppTheme.spacing
    val title = order.receipt?.let { stringResource(Res.string.station_kasir_detail_title, it) } ?: stringResource(Res.string.station_kasir_detail_plain)
    val info: @Composable () -> Unit = {
        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            ListCard {
                DividedItems(
                    listOfNotNull(
                        stringResource(Res.string.station_kasir_type) to placeOf(order),
                        order.customerName?.let { stringResource(Res.string.receipt_customer) to it },
                        stringResource(Res.string.station_kasir_time) to DateTimeFormat.stamp(order.createdAt)?.let { whenLabel(it) }.orEmpty(),
                        order.cashierName?.let { stringResource(Res.string.receipt_cashier) to it },
                        order.paymentLabel?.let { stringResource(Res.string.station_kasir_payment) to it },
                        order.note?.let { stringResource(Res.string.station_kasir_note) to it },
                    ),
                ) { (label, value) -> DetailRow(label = label, value = value) }
            }
            order.pendingCancel?.let { request ->
                InlineMessage(text = listOfNotNull(stringResource(Res.string.station_locked_by, request.requestedByName.orEmpty()), request.reason).joinToString(": "))
            }
        }
    }
    val lines: @Composable () -> Unit = {
        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            ListCard {
                DividedItems(order.lines) { line ->
                    ListRow(
                        title = "${line.quantity}× ${line.name}",
                        caption = line.details.joinToString(" · ").ifBlank { null },
                        footnote = line.note?.let { stringResource(Res.string.cashier_line_note, it) },
                        trailing = { AppText(text = formatRupiah(line.subtotal)) },
                    )
                }
            }
            ListCard {
                if (order.discount > 0) DetailRow(label = stringResource(Res.string.station_kasir_discount), value = "−${formatRupiah(order.discount)}")
                DetailRow(label = stringResource(Res.string.cashier_total), value = formatRupiah(order.total))
            }
            Actions(order = order, state = state, viewModel = viewModel, canWithdraw = canWithdraw)
        }
    }

    // Satu kolom selebar layar seperti halaman turunan lain; keadaan pesanan ikut di baris judul.
    PlatformBackHandler(enabled = true, onBack = viewModel::close)
    Column(modifier = modifier.fillMaxSize()) {
        SubPageHeader(
            title = title,
            back = HeaderBack(stringResource(Res.string.back_to_page, listTitle), viewModel::close),
            width = HeaderWidth.Page,
            trailing = { StatusOf(order) },
        )
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(AppTheme.windowSize.pagePadding),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            info()
            lines()
        }
    }
}

@Composable
private fun Actions(order: CashierOrder, state: CashierOrdersState, viewModel: CashierOrdersViewModel, canWithdraw: (CashierCancellation) -> Boolean) {
    val spacing = AppTheme.spacing
    Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        // Kasir memilih kertas yang dicetak ulang; struk stasiun hanya untuk stasiun tanpa tablet yang punya menu di pesanan ini.
        val plan = viewModel.printPlan()
        viewModel.reprintSlots(order).forEach { slot ->
            if (slot == PrinterSlot.Receipt) {
                PrimaryButton(text = stringResource(Res.string.station_kasir_reprint), onClick = { viewModel.reprint(slot) }, loading = state.printing == slot, enabled = state.printing == null)
            } else {
                SecondaryButton(
                    text = stringResource(Res.string.station_kasir_reprint_station, printerSlotName(slot, plan)),
                    onClick = { viewModel.reprint(slot) },
                    loading = state.printing == slot,
                    enabled = state.printing == null,
                )
            }
        }
        state.reprint?.let { status ->
            val printer = printerSlotName(status.slot, plan)
            when (status.result) {
                ReprintResult.Printed -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_done, printer), tone = MessageTone.Success)
                ReprintResult.NoPrinter -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_no_printer, printer))
                ReprintResult.Failed -> InlineMessage(text = stringResource(Res.string.station_kasir_reprint_failed, printer))
            }
        }
        if (!order.voided) {
            val pending = order.pendingCancel
            if (pending == null) {
                SecondaryButton(text = stringResource(Res.string.station_cancel_request), onClick = viewModel::askCancel, tone = ButtonTone.Danger, enabled = !state.cancelling)
                AppText(text = stringResource(Res.string.station_kasir_cancel_hint), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            } else if (canWithdraw(pending)) {
                SecondaryButton(text = stringResource(Res.string.station_withdraw), onClick = viewModel::withdrawCancel, tone = ButtonTone.Cancel, loading = state.cancelling, enabled = !state.cancelling)
            }
            if (!state.askingCancel) state.cancelFailure?.let { InlineMessage(text = failureText(it)) }
        }
    }
}

