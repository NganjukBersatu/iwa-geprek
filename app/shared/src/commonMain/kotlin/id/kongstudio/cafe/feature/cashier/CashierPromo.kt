package id.kongstudio.cafe.feature.cashier

private const val KindBasic = "basic"
private const val KindTotal = "total"
private const val KindProduct = "produk"
private const val TypePercent = "persen"
private const val TypeNominal = "nominal"
private const val ActivationAutomatic = "otomatis"
// Nilai persen disimpan dua desimal di server; dihitung dalam perseratus persen supaya pembulatannya sama persis.
private const val HundredthsPerWhole = 10_000L
private const val HalfHundredths = 5_000L

/** Promo potongan untuk kasir, bertanggal "YYYY-MM-DD" WIB, dengan [valueHundredths] nilai potongan dikali 100 (persen atau rupiah). */
internal class CashierPromo(
    val id: String,
    val name: String,
    val kind: String,
    val discountType: String,
    val valueHundredths: Long,
    val productIds: Set<String>,
    val minimumSpend: Long?,
    val activation: String,
    val startsOn: String,
    val endsOn: String,
) {
    val automatic: Boolean get() = activation == ActivationAutomatic

    /** Kedua ujung tanggal ikut berlaku, sama seperti server. */
    fun inEffect(day: String): Boolean = day in startsOn..endsOn

    /** Menu ini mendapat potongan dari promo menu; dipakai untuk label dan tab Promo. */
    fun covers(menuId: String): Boolean = kind == KindProduct && menuId in productIds

    /** Cermin `app.core.orders.promo.discount_of`: dasar promo menu adalah harga menu tanpa ekstra, promo lain memakai subtotal. */
    fun discountOf(lines: List<CartLine>, day: String): Long {
        if (!inEffect(day)) return 0
        val subtotal = lines.sumOf { it.subtotal }
        val basis = when (kind) {
            KindBasic -> subtotal
            KindTotal -> if (minimumSpend != null && subtotal < minimumSpend) return 0 else subtotal
            KindProduct -> lines.filter { it.item.id in productIds }.sumOf { it.item.price * it.quantity }
            else -> return 0
        }
        if (basis <= 0) return 0
        return when (discountType) {
            TypePercent -> (basis * valueHundredths + HalfHundredths) / HundredthsPerWhole
            TypeNominal -> minOf((valueHundredths + 50) / 100, basis)
            else -> 0
        }
    }
}

/** Promo otomatis pertama yang mencakup menu ini, menurut urutan server, supaya semua tablet memilih promo yang sama. */
internal fun List<CashierPromo>.automaticFor(menuId: String, day: String): CashierPromo? =
    firstOrNull { it.automatic && it.inEffect(day) && it.covers(menuId) }

/** Promo yang berlaku hari ini, untuk pilihan di keranjang. */
internal fun CashierUiState.promosToday(day: String): List<CashierPromo> = promos.filter { it.inEffect(day) }

/** Promo pesanan ini: pilihan kasir, atau promo otomatis dari menu pertama di keranjang selama kasir tidak memilih "Tanpa promo". */
internal fun CashierUiState.promoFor(lines: List<CartLine>, day: String): CashierPromo? {
    promoId?.let { id -> return promos.firstOrNull { it.id == id && it.inEffect(day) } }
    if (promoOff) return null
    return lines.firstNotNullOfOrNull { promos.automaticFor(it.item.id, day) }
}

/** Menu yang mendapat potongan dari promo menu hari ini, untuk label dan tab Promo. */
internal fun CashierUiState.promoMenuIds(day: String): Set<String> =
    items.filter { item -> promos.any { it.inEffect(day) && it.covers(item.id) } }.map { it.id }.toSet()
