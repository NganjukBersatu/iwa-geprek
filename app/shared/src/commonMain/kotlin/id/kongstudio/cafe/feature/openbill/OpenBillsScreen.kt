package id.kongstudio.cafe.feature.openbill

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.cashier.CartLine
import id.kongstudio.cafe.feature.cashier.CashierViewModel
import id.kongstudio.cafe.feature.cashier.PaymentSheet
import id.kongstudio.cafe.feature.cashier.PaymentSummary
import id.kongstudio.cafe.feature.cashier.PlacedOrder
import id.kongstudio.cafe.feature.cashier.ReceiptPrintView
import id.kongstudio.cafe.feature.cashier.TicketPrint
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.feature.stationboard.CashierOrder
import id.kongstudio.cafe.offline.newClientId
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.bill_add_menu
import id.kongstudio.cafe.resources.bill_cancel
import id.kongstudio.cafe.resources.bill_cancel_message
import id.kongstudio.cafe.resources.bill_cancel_reason
import id.kongstudio.cafe.resources.bill_cancel_title
import id.kongstudio.cafe.resources.bill_empty
import id.kongstudio.cafe.resources.bill_not_mine
import id.kongstudio.cafe.resources.bill_pay
import id.kongstudio.cafe.resources.bill_row_caption
import id.kongstudio.cafe.resources.bill_search
import id.kongstudio.cafe.resources.bill_subtotal
import id.kongstudio.cafe.resources.bill_table
import id.kongstudio.cafe.resources.bill_take_away
import id.kongstudio.cafe.resources.bill_untitled
import id.kongstudio.cafe.resources.bill_total_due
import id.kongstudio.cafe.resources.cashier_discount
import id.kongstudio.cafe.resources.cashier_no_promo
import id.kongstudio.cafe.resources.cashier_promo
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.subpage.SubPage
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

/** Bill yang sudah dikerjakan dapur tetapi belum dibayar: semua bill cabang tampil, dan hanya pemilik sesinya yang mengubah atau membayarnya. */
@Composable
internal fun OpenBillsScreen(
    title: String,
    viewModel: PagedListViewModel<CashierOrder>,
    repository: OpenBillRepository,
    cashier: CashierViewModel,
    onAddMenu: (CashierOrder) -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var openId by remember { mutableStateOf<String?>(null) }
    // Bill yang baru dibayar hilang dari daftar, tetapi layar suksesnya masih tampil: yang terakhir terlihat dipakai sampai kasir menutupnya.
    var lastSeen by remember { mutableStateOf<CashierOrder?>(null) }
    val fromList = openId?.let { id -> state.items.firstOrNull { it.id == id } }
    if (fromList != null) lastSeen = fromList
    val opened = fromList ?: lastSeen?.takeIf { it.id == openId }

    if (opened != null) {
        OpenBillPage(bill = opened, listTitle = title, viewModel = viewModel, repository = repository, cashier = cashier, onAddMenu = onAddMenu, onBack = { openId = null }, modifier = modifier)
        return
    }

    ResourceList(
        title = title,
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.bill_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.bill_search),
        query = state.query,
        onQueryChange = viewModel::setQuery,
    ) { bill ->
        ListRow(
            title = billTitle(bill),
            caption = stringResource(Res.string.bill_row_caption, bill.cashierName.orEmpty(), DateTimeFormat.stampAt(isoEpoch(bill.createdAt)).time),
            footnote = if (bill.mine) null else stringResource(Res.string.bill_not_mine),
            trailing = { AppText(text = formatRupiah(bill.total), role = TextRole.Title) },
            opensDetail = true,
            onClick = { openId = bill.id },
        )
    }
}

@Composable
private fun OpenBillPage(
    bill: CashierOrder,
    listTitle: String,
    viewModel: PagedListViewModel<CashierOrder>,
    repository: OpenBillRepository,
    cashier: CashierViewModel,
    onAddMenu: (CashierOrder) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier,
) {
    val state by viewModel.state.collectAsState()
    val cashierState by cashier.state.collectAsState()
    val scope = rememberCoroutineScope()
    var promoId by remember(bill.id) { mutableStateOf<String?>(null) }
    var quote by remember(bill.id) { mutableStateOf<BillQuote?>(null) }
    var paying by remember { mutableStateOf(false) }
    var cancelling by remember { mutableStateOf(false) }
    var reason by remember { mutableStateOf("") }
    var placed by remember { mutableStateOf<PlacedOrder?>(null) }
    var settled by remember { mutableStateOf<CashierOrder?>(null) }
    var paidWith by remember { mutableStateOf<String?>(null) }
    var printView by remember { mutableStateOf(receiptView(printing = false)) }
    val settleKey = remember(paying) { newClientId() }
    val failure = state.actionFailure?.let { failureText(it) }
    val promos = cashierState.promos

    // Potongan dihitung server, bukan tablet, setiap promo atau isi bill berubah.
    LaunchedEffect(bill.id, bill.version, promoId) {
        if (bill.mine) quote = (repository.quote(bill, promoId) as? DeviceResult.Ok)?.value
    }
    val shown = quote
    val total = shown?.total ?: bill.total

    SubPage(
        title = billTitle(bill),
        backLabel = stringResource(Res.string.back_to_page, listTitle),
        onBack = onBack,
        modifier = modifier,
        canLeave = !state.acting,
    ) {
        DetailCard(
            rows = listOf(
                stringResource(Res.string.bill_subtotal) to formatRupiah(shown?.subtotal ?: bill.total),
                (shown?.promoName?.let { stringResource(Res.string.cashier_discount, it) }.orEmpty()) to shown?.discount?.takeIf { it > 0 }?.let { "-" + formatRupiah(it) },
                stringResource(Res.string.bill_total_due) to formatRupiah(total),
            ),
        )
        bill.lines.forEach { line ->
            ListRow(
                title = "${line.quantity}× ${line.name}",
                caption = (line.details + listOfNotNull(line.note)).joinToString(" · ").ifEmpty { null },
                trailing = { AppText(text = formatRupiah(line.subtotal), role = TextRole.Body) },
            )
        }
        if (!bill.mine) {
            InlineMessage(text = stringResource(Res.string.bill_not_mine))
            return@SubPage
        }
        if (promos.isNotEmpty()) {
            val options = listOf(stringResource(Res.string.cashier_no_promo)) + promos.map { it.name }
            val selected = promos.indexOfFirst { it.id == promoId }.takeIf { it >= 0 }?.plus(1) ?: 0
            ChoiceFlow(
                label = stringResource(Res.string.cashier_promo),
                options = options,
                selectedIndex = selected,
                onSelect = { index -> promoId = promos.getOrNull(index - 1)?.id },
            )
        }
        if (!paying && !cancelling) failure?.let { InlineMessage(text = it) }
        Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            SecondaryButton(
                text = stringResource(Res.string.bill_cancel),
                onClick = {
                    viewModel.clearActionFailure()
                    cancelling = true
                },
                tone = ButtonTone.Danger,
                modifier = Modifier.weight(1f),
            )
            SecondaryButton(
                text = stringResource(Res.string.bill_add_menu),
                onClick = { onAddMenu(bill) },
                modifier = Modifier.weight(1f),
            )
            PrimaryButton(
                text = stringResource(Res.string.bill_pay),
                onClick = {
                    viewModel.clearActionFailure()
                    paying = true
                },
                modifier = Modifier.weight(1f),
            )
        }
    }

    if (paying) {
        val catalog = cashierState.items.associateBy { it.id }
        val lines = bill.lines.mapNotNull { line ->
            val item = catalog[line.menuItemId] ?: return@mapNotNull null
            CartLine(
                key = "${line.menuItemId}|${line.name}|${line.note.orEmpty()}",
                item = item,
                quantity = line.quantity,
                details = line.details,
                variants = line.variants,
                note = line.note,
                unitPrice = line.unitPrice,
            )
        }
        PaymentSheet(
            summary = PaymentSummary(lines = lines, promoName = shown?.promoName, discount = shown?.discount ?: 0, total = total, subtotalOverride = shown?.subtotal ?: bill.total),
            methods = cashierState.methods,
            submitting = state.acting,
            failure = state.actionFailure,
            placed = placed,
            placedMethod = cashierState.methods.firstOrNull { it.code == paidWith },
            print = printView,
            tickets = TicketPrint(printing = false, printed = true, failures = emptyList(), available = false),
            onPrintTickets = {},
            onReprint = {
                scope.launch {
                    printView = receiptView(printing = true)
                    val paid = settled ?: return@launch
                    val report = cashier.reprint(paid.toPrintable(cashier::categoryOfMenu), PrinterSlot.Receipt)
                    printView = receiptView(printing = false, reported = true, printedAny = report.printedAny, failed = report.failures.keys.map { it.key })
                }
            },
            onConfirm = { code, cash ->
                paidWith = code
                viewModel.act(onSuccess = {}) {
                    val result = repository.settle(bill, code, cash, promoId, settleKey)
                    if (result is DeviceResult.Ok) {
                        settled = result.value
                        placed = PlacedOrder(bill.receipt, result.value.total, ((cash ?: result.value.total) - result.value.total).coerceAtLeast(0))
                        scope.launch {
                            printView = receiptView(printing = true)
                            val report = cashier.reprint(result.value.toPrintable(cashier::categoryOfMenu), PrinterSlot.Receipt)
                            printView = receiptView(printing = false, reported = true, printedAny = report.printedAny, failed = report.failures.keys.map { it.key })
                        }
                    }
                    result
                }
            },
            onDismiss = {
                val done = placed != null
                viewModel.clearActionFailure()
                paying = false
                placed = null
                settled = null
                if (done) onBack()
            },
        )
    }

    if (cancelling) {
        ConfirmSheet(
            title = stringResource(Res.string.bill_cancel_title),
            message = stringResource(Res.string.bill_cancel_message),
            confirmLabel = stringResource(Res.string.bill_cancel),
            destructive = true,
            enabled = !state.acting,
            onConfirm = {
                viewModel.act(onSuccess = {
                    cancelling = false
                    onBack()
                }) { repository.cancel(bill, reason) }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                cancelling = false
            },
            notice = {
                AppTextField(value = reason, onValueChange = { reason = it }, label = stringResource(Res.string.bill_cancel_reason))
                failure?.let { InlineMessage(text = it) }
            },
        )
    }
}

private fun isoEpoch(iso: String): Long = id.kongstudio.cafe.feature.stationboard.isoToEpoch(iso) ?: 0L

// Tablet Mode Kasir mencetak ulang dari sini, jadi layar sukses menunjuk tombol cetak ulang miliknya.
private fun receiptView(printing: Boolean, reported: Boolean = false, printedAny: Boolean = false, failed: List<String> = emptyList()) =
    ReceiptPrintView(printing = printing, reported = reported, printedAny = printedAny, unpaired = emptyList(), failed = failed, fromHistory = true)

/** Nomor nota dan tempat duduk, hanya yang terisi: bill yang belum bernomor tidak diawali tanda pemisah. */
@Composable
private fun billTitle(bill: CashierOrder): String {
    val place = if (bill.takeAway) stringResource(Res.string.bill_take_away) else bill.tableNo?.let { stringResource(Res.string.bill_table, it) }
    return listOfNotNull(bill.receipt, place).joinToString(" · ").ifEmpty { stringResource(Res.string.bill_untitled) }
}
