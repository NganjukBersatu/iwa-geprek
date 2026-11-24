package id.kongstudio.cafe.feature.cashier

/** Keadaan menu di kasir; hanya [Ready] yang bisa dipesan. */
internal enum class ItemStatus { Ready, SoldOut, IngredientOut, NoRecipe }

// Tabel yang menentukan apa yang tampil dan bisa dipesan di kasir; perubahannya memuat ulang katalog lewat /v2/live.
internal val CashierMenuTables = setOf(
    "menu_items", "menu_outlet_prices", "categories", "ingredients", "recipe_ingredients", "stock_items",
    "variant_groups", "variant_choices", "menu_variant_groups", "extras", "extra_outlet_prices", "menu_extras",
)

// Data pendukung kasir yang diubah dari web: promo, cara bayar, identitas struk, pilihan pengunjung, dan catatan pesanan.
internal val CashierReferenceTables = setOf(
    "promos", "payment_methods", "cafe_settings", "visitor_categories", "visitor_genders", "categories",
)

internal class VariantOption(val id: String, val name: String)

internal class VariantGroup(
    val id: String,
    val name: String,
    val required: Boolean,
    val options: List<VariantOption>,
)

internal class ExtraOption(val id: String, val name: String, val price: Long)

internal class CashierItem(
    val id: String,
    val name: String,
    val category: String,
    /** UUID kategori menu; null untuk menu tanpa kategori, yang tidak pernah dicetak di printer Bar atau Dapur. */
    val categoryId: String?,
    val price: Long,
    val imageUrl: String? = null,
    val status: ItemStatus = ItemStatus.Ready,
    val variants: List<VariantGroup> = emptyList(),
    val extras: List<ExtraOption> = emptyList(),
) {
    val orderable: Boolean get() = status == ItemStatus.Ready

    /** Menu yang perlu pilihan varian atau ekstra sebelum masuk pesanan. */
    val needsChoice: Boolean get() = variants.isNotEmpty() || extras.isNotEmpty()
}

/** Satu ekstra pada baris pesanan; [price] harga satuannya. */
internal class PickedExtra(val name: String, val count: Int, val price: Long)

internal class CartLine(
    val key: String,
    val item: CashierItem,
    val quantity: Int,
    /** Nama pilihan varian dan ekstra yang melekat pada baris ini, untuk ditampilkan. */
    val details: List<String>,
    /** Varian dan ekstra terpisah, karena struk mencetaknya beda tanda ("*" dan "+") dan ekstra berharga ikut dicetak. */
    val variants: List<String> = emptyList(),
    val extras: List<PickedExtra> = emptyList(),
    val note: String?,
    /** Harga satu porsi termasuk ekstra. */
    val unitPrice: Long,
) {
    val subtotal: Long get() = unitPrice * quantity
}
