package id.kongstudio.cafe.feature.cashier

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.failure.printFailedText
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.sound.AppSound
import id.kongstudio.cafe.core.sound.rememberSoundPlayer
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_bill_total
import id.kongstudio.cafe.resources.cashier_cash_received
import id.kongstudio.cafe.resources.cashier_short_by
import id.kongstudio.cafe.resources.cashier_overpaid_hint
import id.kongstudio.cafe.resources.cashier_overpaid
import id.kongstudio.cafe.resources.cashier_change_label
import id.kongstudio.cafe.resources.cashier_cash_exact
import id.kongstudio.cafe.resources.cashier_bank_received
import id.kongstudio.cafe.resources.cashier_direct_customer
import id.kongstudio.cafe.resources.cashier_discount
import id.kongstudio.cafe.resources.cashier_kitchen_bar
import id.kongstudio.cafe.resources.cashier_line_note
import id.kongstudio.cafe.resources.cashier_method_none
import id.kongstudio.cafe.resources.cashier_method_none_ready
import id.kongstudio.cafe.resources.cashier_method_ready
import id.kongstudio.cafe.resources.cashier_method_unready
import id.kongstudio.cafe.resources.cashier_method_unready_item
import id.kongstudio.cafe.resources.cashier_method_unready_reason
import id.kongstudio.cafe.resources.cashier_order_summary
import id.kongstudio.cafe.resources.cashier_pay_need_cash
import id.kongstudio.cafe.resources.cashier_pay_need_method
import id.kongstudio.cafe.resources.cashier_pay_short
import id.kongstudio.cafe.resources.cashier_payment_pick
import id.kongstudio.cafe.resources.cashier_payment_title
import id.kongstudio.cafe.resources.cashier_process_pay
import id.kongstudio.cafe.resources.cashier_processing
import id.kongstudio.cafe.resources.cashier_show_customer
import id.kongstudio.cafe.resources.cashier_show_customer_hint
import id.kongstudio.cafe.resources.cashier_subtotal
import id.kongstudio.cafe.resources.cashier_receipt_missing
import id.kongstudio.cafe.resources.cashier_tickets_printed
import id.kongstudio.cafe.resources.receipt_printing
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.appdialog.AppDialogWidth
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.choicetile.ChoiceTile
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

private const val MethodColumns = 2

// Kode tunai milik server (app.models.order.CASH_METHOD): satu-satunya metode yang memberi kembalian uang.
internal const val CashMethodCode = "tunai"

/** Isi pesanan seperti di keranjang, untuk kolom ringkasan layar bayar. */
internal class PaymentSummary(
    val lines: List<CartLine>,
    val promoName: String?,
    val discount: Long,
    val total: Long,
    /** Subtotal dari server untuk bill, yang barisnya bisa lebih sedikit dari isinya bila menunya sudah hilang dari katalog. */
    val subtotalOverride: Long? = null,
) {
    val subtotal: Long get() = subtotalOverride ?: lines.sumOf { it.subtotal }

    val hasContent: Boolean get() = subtotalOverride != null || lines.isNotEmpty()
}

/** Tiket dapur/bar yang dicetak dari layar bayar sebelum pelanggan membayar; [failures] nama printer yang gagal. */
/** [available] salah di Mode Stasiun, karena struk pesanan dicetak tablet stasiun. */
internal class TicketPrint(
    val printing: Boolean,
    val printed: Boolean,
    val failures: List<String>,
    val available: Boolean = true,
    /** Nomor nota belum didapat; penjualan tetap jalan dan pesannya menyebut akibatnya pada tiket. */
    val receiptFailure: AppFailure? = null,
)

/** Pembayaran satu pesanan dalam modal dua kolom seperti kasir web yang berganti ke [PaymentCelebration] dan memutar suara berhasil setelah tersimpan. */
@Composable
internal fun PaymentSheet(
    summary: PaymentSummary,
    methods: List<PaymentMethod>,
    submitting: Boolean,
    failure: AppFailure?,
    placed: PlacedOrder?,
    placedMethod: PaymentMethod?,
    print: ReceiptPrintView,
    tickets: TicketPrint,
    onPrintTickets: () -> Unit,
    onReprint: () -> Unit,
    onConfirm: (code: String, cashReceived: Long?) -> Unit,
    onDismiss: () -> Unit,
) {
    val spacing = AppTheme.spacing
    val wide = AppTheme.windowSize.isWide
    val sound = rememberSoundPlayer()
    var methodCode by rememberSaveable { mutableStateOf(methods.firstOrNull { it.ready }?.code) }
    var cash by rememberSaveable { mutableStateOf<Long?>(null) }
    var showingCustomer by rememberSaveable { mutableStateOf(false) }
    val method = methods.firstOrNull { it.code == methodCode }
    val needsCash = method?.needsChange == true
    val received = cash
    // Total nol (promo 100%) tidak menagih uang, jadi kasir tidak diminta mengisi uang diterima.
    val shortfall = needsCash && summary.total > 0 && (received == null || received < summary.total)

    LaunchedEffect(placed) { if (placed != null) sound.play(AppSound.PaymentSuccess) }

    if (placed != null) {
        PaymentCelebration(
            placed = placed,
            method = placedMethod,
            print = print,
            onReprint = onReprint,
            onDone = onDismiss,
        )
        return
    }

    AppDialog(
        title = stringResource(Res.string.cashier_payment_title),
        onDismiss = onDismiss,
        maxWidth = AppDialogWidth.Wide,
        dismissible = !submitting,
    ) {
        val pickPane: @Composable ColumnScope.() -> Unit = {
            MethodPane(
                methods = methods,
                method = method,
                onMethod = { methodCode = it },
                cash = cash,
                onCash = { cash = it },
                total = summary.total,
                onShowCustomer = { showingCustomer = true },
            )
        }
        val summaryPane: @Composable ColumnScope.() -> Unit = {
            SummaryPane(
                summary = summary,
                tickets = tickets,
                onPrintTickets = onPrintTickets,
                failure = failure,
                submitting = submitting,
                canPay = method?.ready == true && !shortfall && summary.hasContent,
                invalidReason = when {
                    method?.ready != true -> stringResource(Res.string.cashier_pay_need_method)
                    needsCash && summary.total > 0 && received == null -> stringResource(Res.string.cashier_pay_need_cash)
                    shortfall -> stringResource(Res.string.cashier_pay_short)
                    else -> null
                },
                onPay = { method?.let { onConfirm(it.code, if (needsCash) cash else null) } },
            )
        }
        if (wide) {
            Row(modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
                Column(
                    modifier = Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(spacing.lg),
                    verticalArrangement = Arrangement.spacedBy(spacing.md),
                    content = pickPane,
                )
                Spacer(Modifier.width(AppTheme.sizes.borderThin).fillMaxHeight().background(AppTheme.colors.divider))
                Column(
                    modifier = Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(spacing.lg),
                    verticalArrangement = Arrangement.spacedBy(spacing.md),
                    content = summaryPane,
                )
            }
        } else {
            Column(modifier = Modifier.fillMaxWidth().verticalScroll(rememberScrollState())) {
                Column(Modifier.padding(spacing.lg), verticalArrangement = Arrangement.spacedBy(spacing.md), content = pickPane)
                AppDivider()
                Column(Modifier.padding(spacing.lg), verticalArrangement = Arrangement.spacedBy(spacing.md), content = summaryPane)
            }
        }
    }

    if (showingCustomer && method?.imageUrl != null) {
        CustomerPayDialog(method = method, total = summary.total, onDismiss = { showingCustomer = false })
    }
}

@Composable
private fun ColumnScope.MethodPane(
    methods: List<PaymentMethod>,
    method: PaymentMethod?,
    onMethod: (String) -> Unit,
    cash: Long?,
    onCash: (Long?) -> Unit,
    total: Long,
    onShowCustomer: () -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    AppText(text = stringResource(Res.string.cashier_payment_pick), role = TextRole.Caption, color = colors.contentMuted)
    if (methods.isEmpty()) {
        InlineMessage(text = stringResource(Res.string.cashier_method_none))
    } else {
        if (methods.none { it.ready }) InlineMessage(text = stringResource(Res.string.cashier_method_none_ready))
        methods.chunked(MethodColumns).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                row.forEach { option ->
                    ChoiceTile(
                        icon = paymentMethodIcon(option.icon),
                        label = option.label,
                        selected = option.code == method?.code,
                        available = option.ready,
                        badge = stringResource(if (option.ready) Res.string.cashier_method_ready else Res.string.cashier_method_unready),
                        onClick = { if (option.ready) onMethod(option.code) },
                        modifier = Modifier.weight(1f),
                    )
                }
                repeat(MethodColumns - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
        // Alasan semua metode yang belum siap dalam satu pesan yang selalu terlihat, tidak menunggu kartunya diketuk.
        val unready = methods.filterNot { it.ready }.map { option ->
            stringResource(Res.string.cashier_method_unready_item, option.label, option.missing.joinToString(", "))
        }
        if (unready.isNotEmpty()) InlineMessage(text = stringResource(Res.string.cashier_method_unready_reason, unready.joinToString("; ")))
    }

    if (method == null) return
    if (method.imageUrl != null) ShowCustomerButton(onClick = onShowCustomer)
    if (method.note.isNotBlank()) {
        AppText(
            text = method.note,
            role = TextRole.Caption,
            color = colors.contentMuted,
            modifier = Modifier.fillMaxWidth().background(colors.background, AppTheme.shapes.field).padding(spacing.md),
        )
    }
    if (method.needsChange) {
        CashReceived(method, cash, onCash, total)
    } else {
        AppText(
            text = stringResource(Res.string.cashier_direct_customer, method.label),
            role = TextRole.Caption,
            color = colors.contentMuted,
            modifier = Modifier.fillMaxWidth().background(colors.background, AppTheme.shapes.field).padding(spacing.md),
        )
    }
}

/** Uang diterima dengan nominal cepat seperti kasir web, dan metode non-tunai yang meminta nominal tidak memberi kembalian karena kelebihannya dicatat server sebagai kelebihan pembayaran. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun CashReceived(method: PaymentMethod, cash: Long?, onCash: (Long?) -> Unit, total: Long) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val nonCash = method.code != CashMethodCode

    MoneyField(
        amount = cash,
        onAmountChange = onCash,
        label = stringResource(if (nonCash) Res.string.cashier_bank_received else Res.string.cashier_cash_received),
        isError = cash != null && cash < total,
    )
    FlowRow(
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        verticalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        quickCashAmounts(total).forEach { amount ->
            AppChip(
                label = if (amount == total) stringResource(Res.string.cashier_cash_exact) else formatRupiah(amount).removePrefix("Rp "),
                selected = cash == amount,
                onClick = { onCash(amount) },
            )
        }
    }
    when {
        cash == null -> Unit
        cash < total -> AmountRow(stringResource(Res.string.cashier_short_by), formatRupiah(total - cash), colors.danger)
        nonCash && cash > total -> {
            AmountRow(stringResource(Res.string.cashier_overpaid), formatRupiah(cash - total), colors.warning)
            AppText(text = stringResource(Res.string.cashier_overpaid_hint), role = TextRole.Caption, color = colors.warning)
        }
        else -> AmountRow(stringResource(Res.string.cashier_change_label), formatRupiah(cash - total), colors.primary)
    }
}

/** Membuka layar QR + total yang aman diputar ke pelanggan. */
@Composable
private fun ShowCustomerButton(onClick: () -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(colors.selected, shape)
            .border(AppTheme.sizes.borderThin, colors.accent, shape)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.md, vertical = spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        AppIcon(icon = AppIcons.Qrcode, tint = colors.primary, size = AppTheme.sizes.icon)
        Column(modifier = Modifier.weight(1f)) {
            AppText(text = stringResource(Res.string.cashier_show_customer), role = TextRole.Label, color = colors.primary)
            AppText(text = stringResource(Res.string.cashier_show_customer_hint), role = TextRole.Caption, color = colors.contentMuted)
        }
        AppIcon(icon = AppIcons.ChevronRight, tint = colors.primary, size = AppTheme.sizes.iconSmall)
    }
}

@Composable
private fun SummaryPane(
    summary: PaymentSummary,
    tickets: TicketPrint,
    onPrintTickets: () -> Unit,
    failure: AppFailure?,
    submitting: Boolean,
    canPay: Boolean,
    invalidReason: String?,
    onPay: () -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var attempted by rememberSaveable { mutableStateOf(false) }

    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        AppText(
            text = stringResource(Res.string.cashier_order_summary),
            role = TextRole.Caption,
            color = colors.contentMuted,
            modifier = Modifier.weight(1f),
        )
        if (tickets.available) {
            AppChip(
                label = stringResource(Res.string.cashier_kitchen_bar),
                icon = AppIcons.Printer,
                selected = false,
                onClick = { if (summary.lines.isNotEmpty() && !tickets.printing) onPrintTickets() },
            )
        }
    }
    when {
        tickets.printing -> AppText(text = stringResource(Res.string.receipt_printing), role = TextRole.Caption, color = colors.contentMuted)
        tickets.failures.isNotEmpty() -> InlineMessage(text = printFailedText(tickets.failures))
        tickets.printed -> InlineMessage(text = stringResource(Res.string.cashier_tickets_printed), tone = MessageTone.Success)
    }
    if (tickets.available && tickets.receiptFailure != null) InlineMessage(text = stringResource(Res.string.cashier_receipt_missing))
    Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        summary.lines.forEach { line -> SummaryLine(line) }
    }
    AppDivider()
    AmountRow(stringResource(Res.string.cashier_subtotal), formatRupiah(summary.subtotal), colors.contentMuted)
    if (summary.discount > 0) {
        AmountRow(stringResource(Res.string.cashier_discount, summary.promoName.orEmpty()), "-${formatRupiah(summary.discount)}", colors.danger)
    }
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        AppText(text = stringResource(Res.string.cashier_bill_total), role = TextRole.Label, color = colors.content, modifier = Modifier.weight(1f))
        AppText(text = formatRupiah(summary.total), role = TextRole.Title, color = colors.primary)
    }
    failure?.let { InlineMessage(text = failureText(it)) }
    if (attempted && !canPay && invalidReason != null) InlineMessage(text = invalidReason)
    PrimaryButton(
        text = stringResource(if (submitting) Res.string.cashier_processing else Res.string.cashier_process_pay),
        onClick = { if (canPay) onPay() else attempted = true },
        enabled = !submitting,
        loading = submitting,
    )
}

@Composable
private fun SummaryLine(line: CartLine) {
    val colors = AppTheme.colors

    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
        Column(modifier = Modifier.weight(1f)) {
            AppText(text = "${line.quantity}x ${line.item.name}", role = TextRole.Body, color = colors.content)
            if (line.details.isNotEmpty()) {
                AppText(text = line.details.joinToString(" · "), role = TextRole.Caption, color = colors.contentMuted)
            }
            line.note?.takeIf { it.isNotBlank() }?.let {
                AppText(text = stringResource(Res.string.cashier_line_note, it), role = TextRole.Caption, color = colors.primary)
            }
        }
        AppText(text = formatRupiah(line.subtotal), role = TextRole.Body, color = colors.content)
    }
}

@Composable
private fun AmountRow(label: String, amount: String, color: Color) {
    Row(modifier = Modifier.fillMaxWidth()) {
        AppText(text = label, role = TextRole.Caption, color = color, modifier = Modifier.weight(1f))
        AppText(text = amount, role = TextRole.Caption, color = color)
    }
}
