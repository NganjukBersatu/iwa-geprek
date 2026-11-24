package id.kongstudio.cafe.ui.theme.window

import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

enum class WindowSize {
    Tiny,
    Compact,
    Medium,
    Expanded;

    val isWide: Boolean
        get() = this == Medium || this == Expanded

    val pagePadding: Dp
        get() = if (isWide) 16.dp else 12.dp

    /** Pengali ukuran seluruh antarmuka; layar lebar sedikit diperkecil, target sentuh tetap minimal 44 dp. */
    val interfaceScale: Float
        get() = if (this == Expanded) 0.92f else 1f

    /** Jumlah kolom kisi pilihan berlebar sama. */
    val choiceColumns: Int
        get() = when (this) {
            Tiny, Compact -> 2
            Medium -> 3
            Expanded -> 4
        }

    companion object {
        fun from(width: Dp): WindowSize = when {
            width <= 360.dp -> Tiny
            width <= 640.dp -> Compact
            width <= 860.dp -> Medium
            else -> Expanded
        }
    }
}
