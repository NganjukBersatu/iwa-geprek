package id.kongstudio.cafe.feature.cashier

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_close
import id.kongstudio.cafe.resources.cashier_customer_total
import id.kongstudio.cafe.resources.cashier_scan_to_pay
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Layar yang diputar ke pelanggan berisi total dan kode bayar tanpa kontrol kasir, dengan total dari angka terbaru agar tetap benar saat promo atau jumlah berubah. */
@Composable
internal fun CustomerPayDialog(method: PaymentMethod, total: Long, onDismiss: () -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    AppDialog(title = stringResource(Res.string.cashier_customer_total), onDismiss = onDismiss) {
        Column(
            modifier = Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(spacing.lg),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            AppText(text = formatRupiah(total), role = TextRole.Display, color = colors.primary)
            method.imageUrl?.let { url ->
                RemoteImage(
                    url = url,
                    contentDescription = method.label,
                    fit = true,
                    modifier = Modifier
                        .widthIn(max = AppTheme.sizes.qrMaxWidth)
                        .fillMaxWidth()
                        .border(AppTheme.sizes.borderThin, colors.divider, AppTheme.shapes.field)
                        .padding(spacing.sm),
                )
            }
            AppText(text = stringResource(Res.string.cashier_scan_to_pay, method.label), role = TextRole.Body, color = colors.contentMuted)
            if (method.note.isNotBlank()) {
                AppText(text = method.note, role = TextRole.Caption, color = colors.contentMuted)
            }
            PrimaryButton(text = stringResource(Res.string.cashier_close), onClick = onDismiss)
        }
    }
}
