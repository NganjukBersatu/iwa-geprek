package id.kongstudio.cafe.ui.theme.spacing

import androidx.compose.runtime.Immutable
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Immutable
class AppSpacing(
    val xs: Dp,
    val sm: Dp,
    val md: Dp,
    val lg: Dp,
    val xl: Dp,
    val xxl: Dp,
    val xxxl: Dp,
    /** Tinggi minimum target sentuh (tombol, input, ikon yang bisa ditekan). */
    val touchTarget: Dp,
    /** Sisi kontrol padat yang berderet (nomor halaman, stepper). */
    val compactTarget: Dp,
)

val DefaultAppSpacing = AppSpacing(
    xs = 4.dp,
    sm = 8.dp,
    md = 12.dp,
    lg = 16.dp,
    xl = 24.dp,
    xxl = 32.dp,
    xxxl = 48.dp,
    touchTarget = 48.dp,
    compactTarget = 36.dp,
)
