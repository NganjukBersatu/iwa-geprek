package id.kongstudio.cafe.feature.sessions

import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.feature.ordersync.PendingOrdersGate
import id.kongstudio.cafe.offline.QueueCounts
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.session_close
import id.kongstudio.cafe.resources.session_confirm_action
import id.kongstudio.cafe.resources.session_confirm_action_sign_out
import id.kongstudio.cafe.resources.session_confirm_message
import id.kongstudio.cafe.resources.session_confirm_title
import id.kongstudio.cafe.resources.session_diff_none
import id.kongstudio.cafe.resources.session_diff_over
import id.kongstudio.cafe.resources.session_diff_short
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.resources.session_close_signs_out
import id.kongstudio.cafe.resources.station_open_orders_warning
import id.kongstudio.cafe.resources.user_close_and_sign_out
import id.kongstudio.cafe.resources.session_form_actual_cash
import id.kongstudio.cafe.resources.session_form_expected_cash
import id.kongstudio.cafe.resources.session_note
import id.kongstudio.cafe.resources.session_part_expected
import id.kongstudio.cafe.resources.session_part_float
import id.kongstudio.cafe.resources.session_part_revenue
import id.kongstudio.cafe.resources.session_part_shopping
import id.kongstudio.cafe.resources.session_three_parts_hint
import id.kongstudio.cafe.core.failure.sessionNeedsNetworkText
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.resources.session_cash_required
import id.kongstudio.cafe.resources.form_invalid_check_above
import org.jetbrains.compose.resources.stringResource

/** Lembar tutup sesi: ditahan sampai antrean pesanan bersih dan rekap server terbaca, lalu satu angka uang di laci atau tiga bagian bila sesinya dibuka dengan uang belanja. */
@Composable
internal fun CloseSessionSheet(
    known: Boolean,
    recap: SessionRecap?,
    queue: QueueCounts?,
    online: Boolean,
    signsOut: Boolean,
    submitting: Boolean,
    failure: AppFailure?,
    onReview: () -> Unit,
    onSubmit: (CountedCash, String) -> Unit,
    onDismiss: () -> Unit,
) {
    var confirming by remember { mutableStateOf(false) }
    var cash by remember { mutableStateOf<Long?>(null) }
    var floatPart by remember { mutableStateOf<Long?>(null) }
    var shoppingPart by remember { mutableStateOf<Long?>(null) }
    var revenuePart by remember { mutableStateOf<Long?>(null) }
    var note by remember { mutableStateOf("") }
    val threeParts = recap?.threeParts == true
    val counted: CountedCash? = when {
        recap == null -> null
        threeParts -> {
            val float = floatPart
            val shopping = shoppingPart
            val revenue = revenuePart
            if (float != null && shopping != null && revenue != null) CountedCash.ThreeParts(float, shopping, revenue) else null
        }
        else -> cash?.let { CountedCash.Single(it) }
    }

    val label = stringResource(if (signsOut) Res.string.user_close_and_sign_out else Res.string.session_close)
    val queueClear = queue?.isEmpty == true

    FormSheet(
        title = label,
        submitLabel = label,
        onSubmit = { if (counted != null) confirming = true },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = known && queueClear && counted != null,
        invalidMessage = stringResource(if (known && queueClear) Res.string.session_cash_required else Res.string.form_invalid_check_above),
        error = failure?.let { failureText(it) },
    ) {
        if (!known) Notice(sessionNeedsNetworkText())
        if (signsOut) {
            AppText(text = stringResource(Res.string.session_close_signs_out), role = TextRole.Body, color = AppTheme.colors.contentMuted)
        }
        PendingOrdersGate(queue = queue, online = online, onReview = onReview)
        recap?.stationOpenOrders?.takeIf { it > 0 }?.let { count ->
            StatusBanner(text = stringResource(Res.string.station_open_orders_warning, count), tone = BannerTone.Warning)
        }
        // Hitung uang baru dibuka setelah antrean bersih, karena rekapnya belum memuat pesanan yang tertahan.
        if (queueClear && recap != null && threeParts) {
            AppText(text = stringResource(Res.string.session_three_parts_hint), role = TextRole.Body, color = AppTheme.colors.contentMuted)
            MoneyInput(stringResource(Res.string.session_part_float), recap.plannedFloat, floatPart) { floatPart = it }
            MoneyInput(stringResource(Res.string.session_part_shopping), recap.plannedShopping, shoppingPart) { shoppingPart = it }
            MoneyInput(stringResource(Res.string.session_part_revenue), recap.expectedRevenue, revenuePart) { revenuePart = it }
        } else if (queueClear) {
            recap?.let {
                AppText(
                    text = stringResource(Res.string.session_form_expected_cash, formatRupiah(it.expectedCash)),
                    role = TextRole.Body,
                    color = AppTheme.colors.contentMuted,
                )
            }
            MoneyField(
                amount = cash,
                onAmountChange = { cash = it },
                label = stringResource(Res.string.session_form_actual_cash),
            )
        }
        if (queueClear) AppTextField(value = note, onValueChange = { note = it }, label = stringResource(Res.string.session_note))
    }

    // Menutup sesi menyangkut uang dan tidak bisa dibalik, jadi selisih kas diperlihatkan lebih dulu.
    if (confirming && counted != null && recap != null) {
        val countedTotal = when (counted) {
            is CountedCash.Single -> counted.actualCash
            is CountedCash.ThreeParts -> counted.actualFloat + counted.actualShopping + counted.actualRevenue
        }
        val expectedTotal = if (threeParts) (recap.plannedFloat ?: 0L) + (recap.plannedShopping ?: 0L) + (recap.expectedRevenue ?: 0L) else recap.expectedCash
        val difference = countedTotal - expectedTotal
        val differenceText = when {
            difference < 0L -> stringResource(Res.string.session_diff_short, formatRupiah(-difference))
            difference > 0L -> stringResource(Res.string.session_diff_over, formatRupiah(difference))
            else -> stringResource(Res.string.session_diff_none)
        }
        ConfirmSheet(
            title = stringResource(Res.string.session_confirm_title),
            message = stringResource(Res.string.session_confirm_message, formatRupiah(countedTotal), formatRupiah(expectedTotal), differenceText),
            confirmLabel = stringResource(if (signsOut) Res.string.session_confirm_action_sign_out else Res.string.session_confirm_action),
            destructive = true,
            enabled = !submitting,
            onConfirm = {
                confirming = false
                onSubmit(counted, note)
            },
            onDismiss = { confirming = false },
        )
    }
}

@Composable
private fun MoneyInput(label: String, expected: Long?, value: Long?, onChange: (Long?) -> Unit) {
    expected?.let {
        AppText(text = stringResource(Res.string.session_part_expected, formatRupiah(it)), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
    }
    MoneyField(amount = value, onAmountChange = onChange, label = label)
}
