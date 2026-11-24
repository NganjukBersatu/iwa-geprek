package id.kongstudio.cafe.ui.component.productcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.compositeOver
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Warna alasan menu tidak bisa dipesan: merah untuk menu habis, oranye untuk bahan habis, abu muda untuk yang belum lengkap diatur. */
enum class BlockedTone { Danger, Warning, Caution }

/** Penanda alasan menu tidak bisa dipesan, sama di kartu Kasir dan daftar Kelola Menu: merah untuk habis, oranye untuk bahan habis, dan pil abu seperti tombol nonaktif untuk yang belum lengkap diatur. */
@Composable
fun BlockedLabel(text: String, tone: BlockedTone, modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    when (tone) {
        BlockedTone.Danger -> PillLabel(text = text, container = colors.danger, content = colors.onPrimary, modifier = modifier)
        BlockedTone.Warning -> PillLabel(text = text, container = colors.warning, content = colors.onPrimary, modifier = modifier)
        BlockedTone.Caution -> PillLabel(text = text, container = colors.primary.copy(alpha = colors.disabledAlpha).compositeOver(colors.surface), content = colors.onPrimary, modifier = modifier)
    }
}

/** Penanda pil kecil satu baris dengan ukuran huruf dan jarak yang sama untuk semua penanda di kartu menu; [border] opsional untuk pil terang. */
@Composable
fun PillLabel(text: String, container: Color, content: Color, modifier: Modifier = Modifier, border: Color? = null) {
    val shape = AppTheme.shapes.pill
    BasicText(
        text = text,
        style = AppTheme.typography.caption.copy(color = content, fontWeight = FontWeight.SemiBold),
        maxLines = 1,
        modifier = modifier
            .clip(shape)
            .background(container)
            .then(if (border != null) Modifier.border(AppTheme.sizes.borderField, border, shape) else Modifier)
            .padding(horizontal = AppTheme.spacing.sm, vertical = AppTheme.spacing.xs),
    )
}
