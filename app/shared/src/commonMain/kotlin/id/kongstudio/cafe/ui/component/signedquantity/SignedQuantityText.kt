package id.kongstudio.cafe.ui.component.signedquantity

import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.ui.theme.AppTheme

/** Jumlah mutasi bertanda di ujung kanan baris: berkurang berwarna bahaya, bertambah berwarna utama. */
@Composable
fun SignedQuantityText(qty: String, unit: String?) {
    val colors = AppTheme.colors
    BasicText(
        text = StockQuantity.signed(qty, unit),
        style = AppTheme.typography.body.copy(fontWeight = FontWeight.SemiBold, color = if (StockQuantity.isNegative(qty)) colors.danger else colors.primary),
    )
}
