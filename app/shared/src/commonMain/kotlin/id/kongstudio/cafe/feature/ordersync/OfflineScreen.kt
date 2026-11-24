package id.kongstudio.cafe.feature.ordersync

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.feature.cashier.CashierItem
import id.kongstudio.cafe.feature.cashier.PaymentMethod
import id.kongstudio.cafe.feature.cashier.PendingLine
import id.kongstudio.cafe.feature.cashier.pendingOrderView
import id.kongstudio.cafe.offline.QueueStatus
import id.kongstudio.cafe.offline.QueuedOrder
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.common_note
import id.kongstudio.cafe.resources.nav_offline
import id.kongstudio.cafe.resources.offline_attempts
import id.kongstudio.cafe.resources.offline_cash_received
import id.kongstudio.cafe.resources.offline_created
import id.kongstudio.cafe.resources.offline_customer
import id.kongstudio.cafe.resources.offline_detail_unreadable
import id.kongstudio.cafe.resources.offline_discard_confirm
import id.kongstudio.cafe.resources.offline_discard_message
import id.kongstudio.cafe.resources.offline_discard_title
import id.kongstudio.cafe.resources.offline_empty
import id.kongstudio.cafe.resources.offline_hint
import id.kongstudio.cafe.resources.offline_menu_unknown
import id.kongstudio.cafe.resources.offline_menus
import id.kongstudio.cafe.resources.offline_needs_login_hint
import id.kongstudio.cafe.resources.offline_no_connection
import id.kongstudio.cafe.resources.offline_order_title
import id.kongstudio.cafe.resources.offline_order_type
import id.kongstudio.cafe.resources.offline_order_type_dine_in
import id.kongstudio.cafe.resources.offline_order_type_take_away
import id.kongstudio.cafe.resources.offline_other_user
import id.kongstudio.cafe.resources.offline_other_user_hint
import id.kongstudio.cafe.resources.offline_payment
import id.kongstudio.cafe.resources.offline_queued_hint
import id.kongstudio.cafe.resources.offline_reason
import id.kongstudio.cafe.resources.offline_receipt
import id.kongstudio.cafe.resources.offline_recorder
import id.kongstudio.cafe.resources.offline_rejected_hint
import id.kongstudio.cafe.resources.offline_report_nothing
import id.kongstudio.cafe.resources.offline_report_rejected
import id.kongstudio.cafe.resources.offline_report_sent
import id.kongstudio.cafe.resources.offline_report_waiting
import id.kongstudio.cafe.resources.offline_send_now
import id.kongstudio.cafe.resources.offline_sending
import id.kongstudio.cafe.resources.offline_status
import id.kongstudio.cafe.resources.offline_status_needs_login
import id.kongstudio.cafe.resources.offline_status_queued
import id.kongstudio.cafe.resources.offline_status_rejected
import id.kongstudio.cafe.resources.offline_status_sending
import id.kongstudio.cafe.resources.offline_summary
import id.kongstudio.cafe.resources.offline_table
import id.kongstudio.cafe.resources.offline_this_account
import id.kongstudio.cafe.resources.offline_total
import id.kongstudio.cafe.resources.sync_item_count
import id.kongstudio.cafe.resources.sync_reason_unknown
import id.kongstudio.cafe.resources.sync_retry
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.subpage.SubPage
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/**
 * Mode Offline: setiap pesanan di antrean tablet dengan keadaannya, Kirim sekarang dengan kabar hasilnya, dan rincian pesanan
 * yang dibuka dari barisnya. [catalog] dan [methods] dari kasir dipakai untuk menamai menu dan metode bayar yang tersimpan sebagai UUID.
 */
@Composable
internal fun OfflineScreen(
    viewModel: OrderSyncViewModel,
    catalog: List<CashierItem>,
    methods: List<PaymentMethod>,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var openId by remember { mutableStateOf<String?>(null) }
    val title = stringResource(Res.string.nav_offline)
    val opened = openId?.let { id -> state.orders.firstOrNull { it.clientId == id } }

    if (opened != null) {
        OrderPage(
            order = opened,
            own = opened.userId == viewModel.ownerId,
            sending = state.sending,
            catalog = catalog,
            methods = methods,
            listTitle = title,
            onRetry = { viewModel.retry(opened.clientId) },
            onDiscard = {
                viewModel.discard(opened.clientId)
                openId = null
            },
            onBack = { openId = null },
            modifier = modifier,
        )
        return
    }

    val counts = state.counts
    val ownWaiting = state.orders.count { it.userId == viewModel.ownerId && it.status != QueueStatus.Rejected }
    val othersWaiting = state.orders.count { it.userId != viewModel.ownerId && it.status != QueueStatus.Rejected }

    PageFrame(modifier = modifier) {
        item { PageTitle(title = title, subtitle = stringResource(Res.string.offline_hint)) }
        if (!state.online) {
            item { StatusBanner(text = stringResource(Res.string.offline_no_connection), tone = BannerTone.Warning) }
        }
        item {
            AppText(
                text = stringResource(Res.string.offline_summary, counts.queued, counts.needsLogin, counts.rejected),
                role = TextRole.Caption,
                color = AppTheme.colors.contentMuted,
            )
        }
        item {
            PrimaryButton(
                text = stringResource(if (state.sending) Res.string.offline_sending else Res.string.offline_send_now),
                onClick = viewModel::syncNow,
                enabled = ownWaiting > 0 && !state.sending,
                loading = state.sending,
                icon = AppIcons.Refresh,
            )
        }
        state.report?.let { report -> item { ReportMessage(report) } }
        if (othersWaiting > 0) {
            item { Notice(stringResource(Res.string.offline_other_user_hint, othersWaiting)) }
        }
        item {
            if (state.orders.isEmpty()) {
                ListCard { ListRow(title = stringResource(Res.string.offline_empty)) }
            } else {
                ListCard {
                    state.orders.asReversed().forEachIndexed { index, order ->
                        if (index > 0) AppDivider()
                        val own = order.userId == viewModel.ownerId
                        ListRow(
                            title = stringResource(Res.string.offline_order_title, clockOf(order.createdEpoch)),
                            detail = listOf(stringResource(Res.string.sync_item_count, order.itemCount), formatRupiah(order.total)).joinToString(" · "),
                            caption = if (own) stringResource(Res.string.offline_this_account) else stringResource(Res.string.offline_other_user),
                            trailing = { QueueBadge(order, sending = state.sending && own) },
                            onClick = { openId = order.clientId },
                            opensDetail = true,
                        )
                    }
                }
            }
        }
    }
}

/** Kabar satu Kirim sekarang; yang terkirim, ditolak, dan masih menunggu disebut terpisah supaya jelas mana yang perlu ditangani. */
@Composable
private fun ReportMessage(report: SyncReport) {
    val parts = buildList {
        if (report.sent > 0) add(stringResource(Res.string.offline_report_sent, report.sent))
        if (report.rejected > 0) add(stringResource(Res.string.offline_report_rejected, report.rejected))
        if (report.waiting > 0) add(stringResource(Res.string.offline_report_waiting, report.waiting))
    }
    InlineMessage(
        text = parts.joinToString(" ").ifEmpty { stringResource(Res.string.offline_report_nothing) },
        tone = if (report.rejected == 0 && report.waiting == 0) MessageTone.Success else MessageTone.Error,
    )
}

@Composable
private fun QueueBadge(order: QueuedOrder, sending: Boolean) {
    when {
        order.status == QueueStatus.Rejected -> StatusBadge(text = stringResource(Res.string.offline_status_rejected), tone = BadgeTone.Danger, icon = AppIcons.Alert)
        order.status == QueueStatus.NeedsLogin -> StatusBadge(text = stringResource(Res.string.offline_status_needs_login), tone = BadgeTone.Warning, icon = AppIcons.User)
        sending -> StatusBadge(text = stringResource(Res.string.offline_status_sending), tone = BadgeTone.Neutral, icon = AppIcons.Refresh)
        else -> StatusBadge(text = stringResource(Res.string.offline_status_queued), tone = BadgeTone.Neutral, icon = AppIcons.Clock)
    }
}

/** Rincian satu pesanan tertunda; hanya pesanan ditolak yang punya aksi, dan membuangnya selalu dikonfirmasi karena tidak bisa dibatalkan. */
@Composable
private fun OrderPage(
    order: QueuedOrder,
    own: Boolean,
    sending: Boolean,
    catalog: List<CashierItem>,
    methods: List<PaymentMethod>,
    listTitle: String,
    onRetry: () -> Unit,
    onDiscard: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var discarding by remember { mutableStateOf(false) }
    val view = remember(order.payload) { pendingOrderView(order.payload) }
    val menus = catalog.associateBy { it.id }
    val statusText = when {
        order.status == QueueStatus.Rejected -> Res.string.offline_status_rejected
        order.status == QueueStatus.NeedsLogin -> Res.string.offline_status_needs_login
        sending && own -> Res.string.offline_status_sending
        else -> Res.string.offline_status_queued
    }
    val statusHint = when (order.status) {
        QueueStatus.Rejected -> Res.string.offline_rejected_hint
        QueueStatus.NeedsLogin -> Res.string.offline_needs_login_hint
        QueueStatus.Queued -> Res.string.offline_queued_hint
    }

    SubPage(
        title = stringResource(Res.string.offline_order_title, clockOf(order.createdEpoch)),
        backLabel = stringResource(Res.string.back_to_page, listTitle),
        onBack = onBack,
        modifier = modifier,
    ) {
        AppText(text = stringResource(statusHint), role = TextRole.Body, color = AppTheme.colors.contentMuted)
        DetailCard(
            rows = listOf(
                stringResource(Res.string.offline_status) to stringResource(statusText),
                stringResource(Res.string.offline_reason) to (order.message ?: stringResource(Res.string.sync_reason_unknown)).takeIf { order.status == QueueStatus.Rejected },
                stringResource(Res.string.offline_created) to DateTimeFormat.stampAt(order.createdEpoch).let { stamp -> "${longDateLabel(stamp.date)}, ${stamp.time}" },
                stringResource(Res.string.offline_recorder) to stringResource(if (own) Res.string.offline_this_account else Res.string.offline_other_user),
                stringResource(Res.string.offline_receipt) to view?.receiptNumber,
                stringResource(Res.string.offline_order_type) to view?.let { stringResource(if (it.takeAway) Res.string.offline_order_type_take_away else Res.string.offline_order_type_dine_in) },
                stringResource(Res.string.offline_customer) to view?.customerName,
                stringResource(Res.string.offline_table) to view?.tableNo,
                stringResource(Res.string.offline_payment) to view?.let { pending -> methods.firstOrNull { it.code == pending.paymentCode }?.label ?: pending.paymentCode },
                stringResource(Res.string.offline_cash_received) to view?.cashReceived?.let(::formatRupiah),
                stringResource(Res.string.offline_total) to formatRupiah(order.total),
                stringResource(Res.string.common_note) to view?.noteLabel,
                stringResource(Res.string.offline_attempts) to order.attempts.toString(),
            ),
        )
        SectionTitle(stringResource(Res.string.offline_menus))
        if (view == null) {
            AppText(text = stringResource(Res.string.offline_detail_unreadable), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        } else {
            ListCard {
                view.lines.forEachIndexed { index, line ->
                    if (index > 0) AppDivider()
                    LineRow(line, menus[line.menuId])
                }
            }
        }
        if (order.status == QueueStatus.Rejected) {
            Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
                SecondaryButton(
                    text = stringResource(Res.string.common_delete),
                    onClick = { discarding = true },
                    tone = ButtonTone.Danger,
                    modifier = Modifier.weight(1f),
                )
                PrimaryButton(text = stringResource(Res.string.sync_retry), onClick = onRetry, enabled = !sending, modifier = Modifier.weight(1f))
            }
        }
    }

    if (discarding) {
        ConfirmSheet(
            title = stringResource(Res.string.offline_discard_title),
            message = stringResource(Res.string.offline_discard_message, formatRupiah(order.total)),
            confirmLabel = stringResource(Res.string.offline_discard_confirm),
            onConfirm = {
                discarding = false
                onDiscard()
            },
            onDismiss = { discarding = false },
            destructive = true,
        )
    }
}

/** Satu menu pesanan dengan varian, ekstra, dan catatannya; menu yang sudah tidak ada di katalog tetap tampil dengan jumlahnya. */
@Composable
private fun LineRow(line: PendingLine, menu: CashierItem?) {
    val variantNames = menu?.variants?.flatMap { it.options }?.filter { it.id in line.variantIds }?.map { it.name }.orEmpty()
    val extraNames = line.extras.mapNotNull { (id, count) ->
        menu?.extras?.firstOrNull { it.id == id }?.let { extra -> if (count > 1) "${extra.name} x$count" else extra.name }
    }
    ListRow(
        title = "${line.quantity}x ${menu?.name ?: stringResource(Res.string.offline_menu_unknown)}",
        detail = (variantNames + extraNames).takeIf { it.isNotEmpty() }?.joinToString(", "),
        caption = line.note?.takeIf { it.isNotBlank() },
    )
}

private fun clockOf(epoch: Long): String = DateTimeFormat.stampAt(epoch).time
