package id.kongstudio.cafe.ui.theme.shape

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Immutable
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.dp

@Immutable
class AppShapes(
    /** Tombol, isian, dan pilihan. */
    val field: Shape,
    val card: Shape,
    /** Modal di tengah layar. */
    val dialog: Shape,
    /** Panel yang menempel di tepi bawah layar (bottom sheet). */
    val sheet: Shape,
    /** Avatar, chip, dan penanda bulat. */
    val pill: Shape,
)

// Skala radius rules 6.6: tombol dan isian 6, kartu 8, modal dan lembar 12 (keputusan Safjar 7 Nov 2026).
val DefaultAppShapes = AppShapes(
    field = RoundedCornerShape(6.dp),
    card = RoundedCornerShape(8.dp),
    dialog = RoundedCornerShape(12.dp),
    sheet = RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp),
    pill = RoundedCornerShape(percent = 50),
)
