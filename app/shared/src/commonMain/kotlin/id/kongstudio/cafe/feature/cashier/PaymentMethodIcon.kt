package id.kongstudio.cafe.feature.cashier

import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Ikon Tabler pilihan admin di web ("ti-qrcode") ke salinan ikonnya di app; nama yang tidak dikenal memakai ikon dompet. */
internal fun paymentMethodIcon(name: String): ImageVector = when (name.removePrefix("ti-")) {
    "cash" -> AppIcons.Cash
    "qrcode" -> AppIcons.Qrcode
    "credit-card" -> AppIcons.CreditCard
    "building-bank" -> AppIcons.BuildingBank
    "device-mobile" -> AppIcons.DeviceMobile
    "receipt" -> AppIcons.Receipt
    "gift" -> AppIcons.Gift
    else -> AppIcons.Wallet
}

/**
 * Warna banjir layar sukses menurut ikon metode, supaya kasir langsung melihat metode apa yang baru dicatat:
 * tunai hijau tua, kode QR dan dompet digital merah muda, bank ungu, sisanya (kartu, voucher, bon) biru.
 */
@Composable
internal fun paymentFloodColor(name: String): Color {
    val colors = AppTheme.colors
    return when (name.removePrefix("ti-")) {
        "cash" -> colors.primary
        "qrcode", "device-mobile" -> colors.rose
        "building-bank" -> colors.violet
        else -> colors.info
    }
}
