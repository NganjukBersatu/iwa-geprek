package id.kongstudio.cafe.ui.theme.typography

import androidx.compose.runtime.Immutable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

@Immutable
class AppTypography(
    val display: TextStyle,
    val headline: TextStyle,
    val section: TextStyle,
    val title: TextStyle,
    val subtitle: TextStyle,
    val body: TextStyle,
    val label: TextStyle,
    val button: TextStyle,
    val caption: TextStyle,
) {
    /** Salinan skala ini dengan satu keluarga huruf untuk semua peran. */
    fun withFontFamily(family: FontFamily) = AppTypography(
        display = display.copy(fontFamily = family),
        headline = headline.copy(fontFamily = family),
        section = section.copy(fontFamily = family),
        title = title.copy(fontFamily = family),
        subtitle = subtitle.copy(fontFamily = family),
        body = body.copy(fontFamily = family),
        label = label.copy(fontFamily = family),
        button = button.copy(fontFamily = family),
        caption = caption.copy(fontFamily = family),
    )
}

// Skala huruf antarmuka (aturan 6.5): ukuran dan tinggi baris dalam sp, ketebalan reguler untuk isi, medium untuk komponen, semibold untuk judul.
// Tinggi baris minimal 1,43 kali ukuran huruf, karena tinggi alami Poppins (naik + turun) 1,424 kali; lebih rendah dari itu ekor g, j, p, q, y terpotong pada teks satu baris.
val DefaultAppTypography = AppTypography(
    display = TextStyle(fontSize = 32.sp, lineHeight = 46.sp, fontWeight = FontWeight.SemiBold),
    headline = TextStyle(fontSize = 28.sp, lineHeight = 40.sp, fontWeight = FontWeight.SemiBold),
    title = TextStyle(fontSize = 24.sp, lineHeight = 35.sp, fontWeight = FontWeight.SemiBold),
    section = TextStyle(fontSize = 20.sp, lineHeight = 29.sp, fontWeight = FontWeight.SemiBold),
    subtitle = TextStyle(fontSize = 16.sp, lineHeight = 23.sp, fontWeight = FontWeight.SemiBold),
    body = TextStyle(fontSize = 14.sp, lineHeight = 20.sp, fontWeight = FontWeight.Normal),
    label = TextStyle(fontSize = 14.sp, lineHeight = 20.sp, fontWeight = FontWeight.Medium),
    button = TextStyle(fontSize = 14.sp, lineHeight = 20.sp, fontWeight = FontWeight.SemiBold),
    caption = TextStyle(fontSize = 12.sp, lineHeight = 18.sp, fontWeight = FontWeight.Normal),
)
