package id.kongstudio.cafe.ui.theme.color

import androidx.compose.ui.graphics.Color

/** Warna dari teks hex "#RRGGBB" atau "#RRGGBBAA" (gaya CSS); null bila tidak terbaca. */
fun parseHexColor(hex: String?): Color? {
    val digits = hex?.trim()?.removePrefix("#") ?: return null
    val value = digits.toLongOrNull(16) ?: return null
    return when (digits.length) {
        6 -> Color(0xFF000000L or value)
        8 -> Color(((value and 0xFF) shl 24) or (value shr 8))
        else -> null
    }
}
