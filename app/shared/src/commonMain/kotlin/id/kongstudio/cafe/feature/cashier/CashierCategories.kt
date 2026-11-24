package id.kongstudio.cafe.feature.cashier

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_all
import id.kongstudio.cafe.resources.cashier_bestseller
import id.kongstudio.cafe.resources.cashier_promo
import org.jetbrains.compose.resources.stringResource

// Awalan "#" membedakan tab bawaan dari nama kategori menu.
internal const val TabBestseller = "#bestseller"
internal const val TabPromo = "#promo"
internal const val TabAll = "#all"

/** Tab kategori kasir: Terlaris dan Promo (bila ada isinya), Semua, lalu tiap kategori menu sesuai abjad. */
internal fun CashierUiState.categoryTabs(): List<String> =
    listOfNotNull(
        TabBestseller.takeIf { bestsellerIds.isNotEmpty() },
        TabPromo.takeIf { promoMenuIds(BusinessDay.today()).isNotEmpty() },
        TabAll,
    ) + items.map { it.category }.distinct().sortedBy { it.lowercase() }

/** Tab yang dipakai: pilihan kasir bila masih ada, selain itu Semua. */
internal val CashierUiState.activeCategory: String
    get() = category.takeIf { it in categoryTabs() } ?: TabAll

/** Menu yang tampil; pencarian menyisir semua menu, bukan hanya tab yang sedang dipilih. */
internal fun CashierUiState.visibleItems(query: String): List<CashierItem> {
    val keyword = query.trim()
    if (keyword.isNotEmpty()) return items.filter { it.name.contains(keyword, ignoreCase = true) }
    return when (val tab = activeCategory) {
        TabBestseller -> {
            val byId = items.associateBy { it.id }
            bestsellerIds.mapNotNull { byId[it] }
        }
        TabPromo -> {
            val ids = promoMenuIds(BusinessDay.today())
            items.filter { it.id in ids }
        }
        TabAll -> items
        else -> items.filter { it.category == tab }
    }
}

@Composable
internal fun categoryLabel(tab: String): String = when (tab) {
    TabBestseller -> stringResource(Res.string.cashier_bestseller)
    TabPromo -> stringResource(Res.string.cashier_promo)
    TabAll -> stringResource(Res.string.cashier_all)
    else -> tab
}
