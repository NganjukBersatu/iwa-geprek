package id.kongstudio.cafe.core.format

fun formatRupiah(amount: Long): String {
    val sign = if (amount < 0) "-" else ""
    val digits = amount.toString().trimStart('-').reversed().chunked(3).joinToString(".").reversed()
    return "${sign}Rp $digits"
}

/** Uang dari server (teks desimal, misalnya "15000.50") menjadi rupiah bulat dengan pembulatan setengah ke atas seperti server, tanpa melewati Double. */
fun rupiahOf(decimal: String): Long {
    val text = decimal.trim()
    val negative = text.startsWith("-")
    val digits = text.removePrefix("-").removePrefix("+")
    // Teks yang bukan angka menjadi 0, bukan aplikasi tertutup.
    val whole = digits.substringBefore('.').ifEmpty { "0" }.toLongOrNull() ?: return 0
    val roundsUp = (digits.substringAfter('.', "").firstOrNull() ?: '0') >= '5'
    val magnitude = if (roundsUp) whole + 1 else whole
    return if (negative) -magnitude else magnitude
}

/** Nilai desimal server (persen atau rupiah) dikali 100, dengan pembulatan yang sama seperti [rupiahOf] dan tanpa melewati Double. */
fun hundredthsOf(decimal: String): Long {
    val text = decimal.trim()
    val negative = text.startsWith("-")
    val digits = text.removePrefix("-").removePrefix("+")
    val whole = digits.substringBefore('.').ifEmpty { "0" }.toLongOrNull() ?: return 0
    val fraction = digits.substringAfter('.', "").padEnd(HundredthsDigits + 1, '0')
    val cents = fraction.take(HundredthsDigits).toLongOrNull() ?: return 0
    val roundsUp = fraction[HundredthsDigits] >= '5'
    val magnitude = whole * HundredthsPerWhole + cents + if (roundsUp) 1 else 0
    return if (negative) -magnitude else magnitude
}

private const val HundredthsDigits = 2
private const val HundredthsPerWhole = 100

/** Rupiah ringkas untuk sumbu grafik, misalnya 150 rb atau 1,5 jt. */
fun formatRupiahCompact(amount: Long): String {
    val abs = kotlin.math.abs(amount)
    val sign = if (amount < 0) "-" else ""
    return when {
        abs >= MILLION -> "$sign${trimmed(abs / MILLION.toDouble())} jt"
        abs >= THOUSAND -> "$sign${trimmed(abs / THOUSAND.toDouble())} rb"
        else -> "$sign$abs"
    }
}

private const val THOUSAND = 1_000L
private const val MILLION = 1_000_000L

private fun trimmed(value: Double): String {
    val tenths = kotlin.math.round(value * 10).toLong()
    val whole = tenths / 10
    val fraction = tenths % 10
    return if (fraction == 0L) whole.toString() else "$whole,$fraction"
}
