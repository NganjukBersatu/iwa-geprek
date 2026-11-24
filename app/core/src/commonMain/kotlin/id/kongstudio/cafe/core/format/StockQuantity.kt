package id.kongstudio.cafe.core.format

private val ValidAmount = Regex("^[0-9]{1,9}([.][0-9]{1,3})?$")

object StockQuantity {
    /** Jumlah yang diketik, dengan koma atau titik, menjadi teks desimal yang diterima server; null bila bukan jumlah yang sah. */
    fun parse(text: String): String? = text.trim().replace(',', '.').takeIf { ValidAmount.matches(it) }

    /** Lebih besar dari nol, untuk catatan masuk, rusak, RnD, dan penyesuaian. */
    fun parsePositive(text: String): String? = parse(text)?.takeIf { (it.toDoubleOrNull() ?: 0.0) > 0.0 }

    /** "10.000" tampil "10", dan "2.500" tampil "2,5", seperti kebiasaan tulisan di sini. */
    fun show(raw: String): String {
        val trimmed = if (raw.contains('.')) raw.trimEnd('0').trimEnd('.') else raw
        return (trimmed.ifEmpty { "0" }).replace('.', ',')
    }

    /** Untuk dibaca saja, dengan pemisah ribuan ("20.000", "1.250,5"); isian ketik tetap memakai [show] supaya titik tidak terbaca sebagai desimal. */
    fun display(raw: String): String {
        val shown = show(raw)
        val negative = shown.startsWith("-")
        val unsigned = shown.removePrefix("-")
        val whole = unsigned.substringBefore(',')
        val fraction = unsigned.substringAfter(',', "")
        val grouped = whole.reversed().chunked(3).joinToString(".").reversed()
        return (if (negative) "-" else "") + grouped + (if (fraction.isEmpty()) "" else ",$fraction")
    }

    fun withUnit(raw: String, unit: String?): String = if (unit.isNullOrBlank()) display(raw) else "${display(raw)} $unit"

    /** Jumlah bertanda supaya arah mutasi terbaca: tambah diberi "+", kurang sudah membawa "-", dan nol tanpa tanda. */
    fun signed(raw: String, unit: String?): String {
        val shown = withUnit(raw, unit)
        val zero = (raw.toDoubleOrNull() ?: 0.0) == 0.0
        return if (zero || shown.startsWith("-")) shown else "+$shown"
    }

    fun isNegative(raw: String): Boolean = (raw.toDoubleOrNull() ?: 0.0) < 0.0

    /**
     * Jumlah kemasan dikali isi kemasan sebagai teks desimal tiga angka di belakang koma, dihitung dengan bilangan bulat
     * supaya tidak ada galat pecahan; null bila salah satu bukan jumlah sah atau hasilnya melewati batas server.
     */
    fun times(count: String, size: String): String? {
        val left = scaled(parse(count) ?: return null) ?: return null
        val right = scaled(parse(size) ?: return null) ?: return null
        if (left <= 0 || right <= 0 || left > MaxScaled / right) return null
        // Hasil berskala 10^6; dibulatkan setengah ke atas ke tiga desimal.
        val product = (left * right + Half) / Scale
        if (product > MaxQuantityScaled) return null
        val whole = product / Scale
        val fraction = (product % Scale).toString().padStart(3, '0').trimEnd('0')
        return if (fraction.isEmpty()) whole.toString() else "$whole.$fraction"
    }

    private fun scaled(text: String): Long? {
        val whole = text.substringBefore('.')
        val fraction = text.substringAfter('.', "").padEnd(3, '0')
        return (whole + fraction).toLongOrNull()
    }

    private const val Scale = 1_000L
    private const val Half = 500L
    private const val MaxScaled = Long.MAX_VALUE - Half
    // Batas jumlah satu catatan di server: 999.999.999 dalam satuan bahan.
    private const val MaxQuantityScaled = 999_999_999_000L
}
