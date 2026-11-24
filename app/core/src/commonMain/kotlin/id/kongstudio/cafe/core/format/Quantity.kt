package id.kongstudio.cafe.core.format

// Mengikuti kolom takaran server Numeric(12,3): paling banyak 9 angka bulat dan 3 angka di belakang koma.
private val Typing = Regex("""^\d{0,9}(?:[.,]\d{0,3})?$""")
private val Complete = Regex("""^(\d{1,9})(?:[.,](\d{1,3}))?$""")

/** Isian takaran yang masih boleh diketik; ketikan yang melewati bentuk kolom ditolak di tempat, bukan dibulatkan diam-diam. */
fun isQuantityTyping(text: String): Boolean = Typing.matches(text)

/** Takaran ketikan (koma atau titik desimal) menjadi teks desimal untuk server tanpa melewati Double, atau null bila tidak terbaca atau tidak lebih dari nol. */
fun quantityOf(typed: String): String? {
    val match = Complete.matchEntire(typed.trim()) ?: return null
    val whole = match.groupValues[1].trimStart('0').ifEmpty { "0" }
    val fraction = match.groupValues[2].trimEnd('0')
    if (whole == "0" && fraction.isEmpty()) return null
    return if (fraction.isEmpty()) whole else "$whole.$fraction"
}
