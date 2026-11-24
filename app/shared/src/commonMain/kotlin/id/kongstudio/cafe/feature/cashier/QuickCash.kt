package id.kongstudio.cafe.feature.cashier

private const val TenThousand = 10_000L
private const val FiftyThousand = 50_000L
private const val HundredThousand = 100_000L

/** Nominal cepat dari gabungan uang kertas: uang pas, total dibulatkan ke puluhan ribu, lalu kelipatan 50.000 dan 100.000 berikutnya (36.000 menjadi 36.000, 40.000, 50.000, 100.000). */
internal fun quickCashAmounts(total: Long): List<Long> {
    if (total <= 0) return emptyList()
    val rounded = roundUp(total, TenThousand)
    val fifty = nextAbove(rounded, FiftyThousand)
    val hundred = nextAbove(fifty, HundredThousand)
    // Total yang sudah bulat membuat pembulatan sama dengan uang pas; yang kembar cukup sekali.
    return listOf(total, rounded, fifty, hundred).distinct()
}

private fun roundUp(amount: Long, step: Long): Long = (amount + step - 1) / step * step

/** Kelipatan [step] terkecil yang lebih besar dari [amount]. */
private fun nextAbove(amount: Long, step: Long): Long = (amount / step + 1) * step
