package id.kongstudio.cafe.ui.theme.window

import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** Kelas lebar jendela saat ini; berubah saat layar diputar. */
enum class WidthClass {
    Tiny,
    Compact,
    Medium,
    Expanded,
}

/** Jenis perangkat untuk tata letak; tetap sama walau layar diputar. */
enum class FormFactor {
    Phone,
    Tablet,
}

/** Ukuran jendela beserta jenis perangkatnya; satu-satunya sumber keputusan tata letak menurut layar. */
data class WindowSize(
    val width: WidthClass,
    val formFactor: FormFactor,
    /** Tinggi jendela sempit, misalnya HP yang dimiringkan, sehingga kepala halaman dibuat ringkas. */
    val short: Boolean,
) {
    val isPhone: Boolean
        get() = formFactor == FormFactor.Phone

    /** Kerangka tablet (rail samping, judul halaman besar); HP tidak pernah memakainya walau dimiringkan. */
    val isWide: Boolean
        get() = !isPhone && (width == WidthClass.Medium || width == WidthClass.Expanded)

    /** Isi boleh dibagi dua kolom berdampingan, termasuk di HP yang dimiringkan. */
    val twoPane: Boolean
        get() = width == WidthClass.Medium || width == WidthClass.Expanded

    val pagePadding: Dp
        get() = if (isWide) 16.dp else 12.dp

    /** Pengali ukuran seluruh antarmuka; hanya tablet lebar yang sedikit diperkecil, target sentuh tetap minimal 44 dp. */
    val interfaceScale: Float
        get() = if (!isPhone && width == WidthClass.Expanded) 0.92f else 1f

    /** Jumlah kolom kisi pilihan berlebar sama. */
    val choiceColumns: Int
        get() = when (width) {
            WidthClass.Tiny, WidthClass.Compact -> 2
            WidthClass.Medium -> 3
            WidthClass.Expanded -> 4
        }

    companion object {
        // Patokan baku Android: sisi terpendek di bawah 600 dp berarti HP.
        private val PhoneMaxSmallestWidth = 600.dp
        private val ShortHeight = 480.dp

        val Default: WindowSize = WindowSize(WidthClass.Compact, FormFactor.Phone, short = false)

        /** [override] berasal dari pengaturan perangkat di web admin; kosong berarti jenisnya ditebak dari sisi terpendek layar. */
        fun from(width: Dp, height: Dp, override: FormFactor? = null): WindowSize {
            val formFactor = override ?: if (minOf(width, height) < PhoneMaxSmallestWidth) FormFactor.Phone else FormFactor.Tablet
            val widthClass = when {
                width <= 360.dp -> WidthClass.Tiny
                width <= 640.dp -> WidthClass.Compact
                width <= 860.dp -> WidthClass.Medium
                else -> WidthClass.Expanded
            }
            return WindowSize(widthClass, formFactor, short = height < ShortHeight)
        }
    }
}
