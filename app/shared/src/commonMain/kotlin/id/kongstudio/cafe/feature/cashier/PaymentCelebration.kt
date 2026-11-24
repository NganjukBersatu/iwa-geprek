package id.kongstudio.cafe.feature.cashier

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.core.failure.printFailedText
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_bank_received
import id.kongstudio.cafe.resources.cashier_bill_total
import id.kongstudio.cafe.resources.cashier_cash_received
import id.kongstudio.cafe.resources.cashier_change_handed
import id.kongstudio.cafe.resources.cashier_change_label
import id.kongstudio.cafe.resources.cashier_done
import id.kongstudio.cafe.resources.cashier_hand_change
import id.kongstudio.cafe.resources.cashier_method
import id.kongstudio.cafe.resources.cashier_no_cash_change
import id.kongstudio.cafe.resources.cashier_overpaid
import id.kongstudio.cafe.resources.cashier_overpaid_hint
import id.kongstudio.cafe.resources.cashier_paid
import id.kongstudio.cafe.resources.cashier_receipt_printed
import id.kongstudio.cafe.resources.cashier_saved
import id.kongstudio.cafe.resources.cashier_saved_offline
import id.kongstudio.cafe.resources.cashier_saved_receipt
import id.kongstudio.cafe.resources.cashier_total_paid
import id.kongstudio.cafe.resources.cashier_understood
import id.kongstudio.cafe.resources.receipt_printer_unpaired
import id.kongstudio.cafe.resources.receipt_printer_unpaired_history
import id.kongstudio.cafe.resources.receipt_printing
import id.kongstudio.cafe.resources.receipt_reprint
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.successtakeover.SuccessTakeover
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Hasil cetak struk untuk layar sukses: [unpaired] dan [failed] berisi nama printer, dan [reported] false selama belum ada hasil. */
internal class ReceiptPrintView(
    val printing: Boolean,
    val reported: Boolean,
    val printedAny: Boolean,
    val unpaired: List<String>,
    val failed: List<String>,
    // Tablet Mode Kasir mencetak ulang dari Riwayat Pesanan karena tidak punya Papan Stasiun.
    val fromHistory: Boolean = false,
)

/** Apa yang harus dilakukan kasir setelah bayar; menentukan judul, angka besar, dan tombol tutup. */
private enum class AfterPayment { HandChange, KeepOverpayment, Paid }

/**
 * Layar penuh setelah pembayaran tersimpan, seperti perayaan absen: warnanya mengikuti metode bayar, judulnya perintah
 * untuk kasir (serahkan kembalian / jangan beri kembalian tunai / lunas), lalu kartu rincian seperti kasir web.
 */
@Composable
internal fun PaymentCelebration(
    placed: PlacedOrder,
    method: PaymentMethod?,
    print: ReceiptPrintView,
    onReprint: () -> Unit,
    onDone: () -> Unit,
) {
    val colors = AppTheme.colors
    val asksAmount = method?.needsChange == true
    // Server menjawab total dan uang diterima; selisihnya kembalian untuk tunai, dana lebih untuk yang lain.
    val received = placed.total + placed.change
    val after = when {
        placed.change > 0 && method != null && method.code != CashMethodCode -> AfterPayment.KeepOverpayment
        placed.change > 0 -> AfterPayment.HandChange
        else -> AfterPayment.Paid
    }
    val amount = if (after == AfterPayment.Paid) placed.total else placed.change

    SuccessTakeover(
        eyebrow = method?.label,
        title = stringResource(
            when (after) {
                AfterPayment.HandChange -> Res.string.cashier_hand_change
                AfterPayment.KeepOverpayment -> Res.string.cashier_no_cash_change
                AfterPayment.Paid -> Res.string.cashier_paid
            },
        ),
        countCaption = stringResource(
            when (after) {
                AfterPayment.HandChange -> Res.string.cashier_change_label
                AfterPayment.KeepOverpayment -> Res.string.cashier_overpaid
                AfterPayment.Paid -> Res.string.cashier_total_paid
            },
        ),
        countTo = amount.coerceAtMost(Int.MAX_VALUE.toLong()).toInt(),
        countLabel = { formatRupiah(it.toLong()) },
        message = when {
            placed.queued -> stringResource(Res.string.cashier_saved_offline)
            placed.receiptNumber != null -> stringResource(Res.string.cashier_saved_receipt, placed.receiptNumber)
            else -> stringResource(Res.string.cashier_saved)
        },
        actionLabel = stringResource(
            when (after) {
                AfterPayment.HandChange -> Res.string.cashier_change_handed
                AfterPayment.KeepOverpayment -> Res.string.cashier_understood
                AfterPayment.Paid -> Res.string.cashier_done
            },
        ),
        containerColor = paymentFloodColor(method?.icon.orEmpty()),
        contentColor = colors.onPrimary,
        onDone = onDone,
        details = {
            DetailCard {
                DetailRow(stringResource(Res.string.cashier_bill_total), formatRupiah(placed.total))
                DetailRow(stringResource(Res.string.cashier_method), method?.label.orEmpty())
                if (asksAmount) {
                    val isCash = after != AfterPayment.KeepOverpayment
                    DetailRow(
                        stringResource(if (isCash) Res.string.cashier_cash_received else Res.string.cashier_bank_received),
                        formatRupiah(received),
                    )
                    DetailRow(
                        stringResource(if (isCash) Res.string.cashier_change_label else Res.string.cashier_overpaid),
                        formatRupiah(placed.change),
                        if (isCash) colors.content else colors.warning,
                    )
                }
            }
            if (after == AfterPayment.KeepOverpayment) {
                AppText(text = stringResource(Res.string.cashier_overpaid_hint), role = TextRole.Caption, color = colors.onPrimary)
            }
            if (print.printing) {
                AppText(text = stringResource(Res.string.receipt_printing), role = TextRole.Caption, color = colors.onPrimary)
            } else if (print.reported) {
                if (print.unpaired.isNotEmpty()) {
                    val text = if (print.fromHistory) Res.string.receipt_printer_unpaired_history else Res.string.receipt_printer_unpaired
                    InlineMessage(text = stringResource(text, print.unpaired.joinToString(", ")))
                }
                if (print.failed.isNotEmpty()) {
                    InlineMessage(text = printFailedText(print.failed))
                    SecondaryButton(text = stringResource(Res.string.receipt_reprint), onClick = onReprint)
                }
                if (print.printedAny && print.unpaired.isEmpty() && print.failed.isEmpty()) {
                    AppText(text = stringResource(Res.string.cashier_receipt_printed), role = TextRole.Caption, color = colors.onPrimary)
                }
            }
        },
    )
}

/** Kartu putih rincian transaksi, seperti di layar sukses kasir web. */
@Composable
private fun DetailCard(content: @Composable () -> Unit) {
    val spacing = AppTheme.spacing
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(AppTheme.colors.surface, AppTheme.shapes.field)
            .padding(spacing.md),
        verticalArrangement = Arrangement.spacedBy(spacing.xs),
    ) { content() }
}

@Composable
private fun DetailRow(label: String, value: String, valueColor: Color = AppTheme.colors.content) {
    Row(modifier = Modifier.fillMaxWidth()) {
        AppText(text = label, role = TextRole.Body, color = AppTheme.colors.contentMuted, modifier = Modifier.weight(1f))
        AppText(text = value, role = TextRole.Label, color = valueColor)
    }
}
