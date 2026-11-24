package id.kongstudio.cafe.feature.expenses

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.AdminJson
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.deposits.DayState
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

internal const val ExpensePageSize = 20
// Tabel yang perubahannya memuat ulang daftar pengeluaran lewat /v2/live.
internal val ExpenseTables = setOf("expenses")
private const val ExpensesPath = "/v2/operational/expenses"
private const val PhotoField = "file"
private const val ReceiptField = "data"
// Batas server per permintaan; daftar disaring di tempat sesudahnya.
private const val ChoiceSize = 50

internal enum class FundSource(val code: String) {
    Drawer("kas_laci"),
    Other("dana_lain"),
    Budget("uang_belanja"),
    ;

    companion object {
        fun of(code: String?): FundSource = entries.firstOrNull { it.code == code } ?: Other
    }
}

internal class ExpenseItem(
    val id: String,
    val outletId: String,
    /** Hari bisnis pengeluaran ini, "YYYY-MM-DD": hari sesinya, atau hari dicatat bila tanpa sesi. */
    val businessDay: String,
    val name: String,
    val amount: Long,
    val source: FundSource,
    val note: String?,
    val buyer: String?,
    val cashier: String?,
    val proofUrl: String?,
    val createdAt: String,
    val shiftId: String?,
    val outletName: String?,
    val ingredientId: String?,
    val ingredientName: String?,
    val quantity: String?,
    val unitName: String?,
)

/** Bahan cabang yang bisa disebut sebuah baris; memilihnya tidak mengubah stok. */
internal class IngredientOption(val id: String, val name: String, val unitName: String?)

/** Karyawan aktif dari cabang mana pun yang bisa dipilih sebagai pembeli. */
internal class BuyerOption(val id: String, val name: String, val outletName: String?)

/** Satu baris nota yang akan dicatat sebagai satu pengeluaran; [ingredientId] menjadikannya baris bahan. */
internal class ReceiptEntry(val name: String, val amount: Long, val ingredientId: String? = null, val quantity: String? = null)

/** Satu baris hasil baca: [ingredient] terisi bila server yakin, selain itu [suggestions] yang mirip. */
internal class ReceiptLine(
    val name: String,
    val amount: Long,
    val quantity: Int?,
    val ingredient: IngredientOption?,
    val suggestions: List<IngredientOption>,
)

/** Hasil membaca foto nota; semua bagian boleh kosong dan tetap diperiksa orang sebelum disimpan. */
internal class ReceiptReading(
    val store: String?,
    val boughtOn: String?,
    val total: Long?,
    val entries: List<ReceiptLine>,
)

/** Jumlah seluruh baris yang cocok dengan penyaring, bukan hanya halaman yang tampil. */
internal data class ExpenseSummary(val total: Long = 0, val fromDrawer: Long = 0)

internal class ExpenseRepository(private val api: AdminApi) {
    private val _summary = MutableStateFlow(ExpenseSummary())
    val summary: StateFlow<ExpenseSummary> = _summary.asStateFlow()

    suspend fun list(request: PageRequest): DeviceResult<ListPage<ExpenseItem>> =
        when (
            val result = api.get(
                path = ExpensesPath,
                serializer = ExpensePageDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to ExpensePageSize,
                    "search" to request.query,
                    "fund_source" to request.filter,
                    "sort" to request.sort,
                    "start" to request.params["from"],
                    "end" to request.params["to"],
                    "user_id" to request.params[ListParam.UserId],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> {
                _summary.value = ExpenseSummary(result.value.totalAmount.toMoney(), result.value.drawerAmount.toMoney())
                DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
            }
        }

    /** Membaca foto nota di server untuk mengisi formulir; belum ada yang disimpan. */
    suspend fun readReceipt(photo: ByteArray): DeviceResult<ReceiptReading> =
        when (val result = api.upload("$ExpensesPath/receipts/read", PhotoField, photo, ReceiptReadingDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    /** Dicari dan dimuat per halaman di server, supaya bahan mana pun tetap terjangkau berapa pun jumlahnya; [page] berbasis nol. */
    suspend fun ingredients(search: String, page: Int): DeviceResult<ChoicePage<IngredientOption>> =
        when (val result = api.get("$ExpensesPath/ingredients", ListSerializer(IngredientOptionDto.serializer()), choiceQuery(search, page))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ChoicePage(result.value.map { it.toModel() }, hasMore = result.value.size == ChoiceSize))
        }

    suspend fun buyers(search: String, page: Int): DeviceResult<ChoicePage<BuyerOption>> =
        when (val result = api.get("$ExpensesPath/buyers", ListSerializer(BuyerOptionDto.serializer()), choiceQuery(search, page))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ChoicePage(result.value.map { BuyerOption(it.id, it.name, it.outletName) }, hasMore = result.value.size == ChoiceSize))
        }

    private fun choiceQuery(search: String, page: Int): Map<String, Any?> = mapOf("size" to ChoiceSize, "page" to page + 1, "search" to search)

    /** Satu nota sekaligus: tiap baris jadi satu pengeluaran di sesi yang sama dan berbagi satu foto. */
    suspend fun record(
        entries: List<ReceiptEntry>,
        source: FundSource,
        buyer: String,
        note: String,
        proof: ByteArray?,
    ): DeviceResult<List<ExpenseItem>> {
        val body = buildJsonObject {
            putJsonArray("items") {
                entries.forEach { entry ->
                    addJsonObject {
                        put("item_name", entry.name.trim())
                        put("amount", entry.amount)
                        entry.ingredientId?.let { put("ingredient_id", it) }
                        entry.quantity?.let { put("quantity", it) }
                    }
                }
            }
            put("fund_source", source.code)
            putText("buyer", buyer)
            putText("note", note)
        }
        return when (
            val result = api.upload(
                path = "$ExpensesPath/receipts",
                field = PhotoField,
                bytes = proof,
                serializer = ListSerializer(ExpenseDto.serializer()),
                fields = mapOf(ReceiptField to AdminJson.encodeToString(JsonElement.serializer(), body)),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() })
        }
    }

    suspend fun update(
        id: String,
        entry: ReceiptEntry,
        source: FundSource,
        buyer: String,
        note: String,
        proof: ByteArray?,
    ): DeviceResult<ExpenseItem> {
        val updated = api.send(
            method = HttpMethod.Patch,
            path = "$ExpensesPath/$id",
            body = buildJsonObject {
                put("item_name", entry.name.trim())
                put("amount", entry.amount)
                // Selalu dikirim: null mengembalikan baris menjadi baris biasa.
                put("ingredient_id", entry.ingredientId)
                put("quantity", entry.quantity)
                put("fund_source", source.code)
                putText("buyer", buyer)
                putText("note", note)
            },
            serializer = ExpenseDto.serializer(),
        )
        if (updated !is DeviceResult.Ok || proof == null) return mapped(updated)
        // Foto yang gagal terunggah dilaporkan sebagai gagal supaya halaman tetap terbuka dan bisa disimpan ulang; isian yang sama aman dikirim lagi.
        return mapped(api.upload("$ExpensesPath/$id/receipt", PhotoField, proof, ExpenseDto.serializer()))
    }

    suspend fun delete(id: String): DeviceResult<Unit> = api.sendUnit(HttpMethod.Delete, "$ExpensesPath/$id")

    /** Hari setoran yang tersentuh: pengeluaran yang akan diubah atau dihapus, atau sesi berjalan bila [expenseIds] kosong (pengeluaran baru). */
    suspend fun dayStates(expenseIds: List<String>): DeviceResult<List<DayState>> =
        when (
            val result = api.send(
                method = HttpMethod.Post,
                path = "$ExpensesPath/day-states",
                body = buildJsonObject {
                    putJsonArray("expense_ids") { expenseIds.forEach { add(JsonPrimitive(it)) } }
                    put("running_session", expenseIds.isEmpty())
                },
                serializer = ListSerializer(DayStateDto.serializer()),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() })
        }

    private fun mapped(result: DeviceResult<ExpenseDto>): DeviceResult<ExpenseItem> = when (result) {
        is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        is DeviceResult.Failed -> result
    }
}

@Serializable
private class ExpensePageDto(
    val items: List<ExpenseDto>,
    val total: Int,
    @SerialName("total_amount") val totalAmount: JsonElement = JsonPrimitive(0),
    @SerialName("drawer_amount") val drawerAmount: JsonElement = JsonPrimitive(0),
)

@Serializable
private class ExpenseDto(
    val id: String,
    @SerialName("outlet_id") val outletId: String,
    @SerialName("business_day") val businessDay: String,
    @SerialName("session_id") val sessionId: String? = null,
    @SerialName("cashier_username") val cashier: String? = null,
    @SerialName("item_name") val name: String,
    val amount: JsonElement,
    @SerialName("fund_source") val source: String,
    val note: String? = null,
    val buyer: String? = null,
    @SerialName("receipt_url") val proofUrl: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("outlet_name") val outletName: String? = null,
    @SerialName("ingredient_id") val ingredientId: String? = null,
    @SerialName("ingredient_name") val ingredientName: String? = null,
    val quantity: JsonElement? = null,
    @SerialName("unit_name") val unitName: String? = null,
) {
    fun toModel() = ExpenseItem(
        id = id,
        outletId = outletId,
        businessDay = businessDay,
        name = name,
        amount = amount.toMoney(),
        source = FundSource.of(source),
        note = note?.takeIf { it.isNotBlank() },
        buyer = buyer?.takeIf { it.isNotBlank() },
        cashier = cashier,
        proofUrl = proofUrl,
        createdAt = createdAt,
        shiftId = sessionId,
        outletName = outletName,
        ingredientId = ingredientId,
        ingredientName = ingredientName,
        quantity = quantity.toQuantity(),
        unitName = unitName,
    )
}

/** "2.500" dari server menjadi "2,5"; kosong bila tidak ada. */
private fun JsonElement?.toQuantity(): String? {
    val raw = (this as? JsonPrimitive)?.content?.takeIf { it.isNotBlank() && it != "null" } ?: return null
    if ('.' !in raw) return raw
    return raw.trimEnd('0').trimEnd('.').replace('.', ',')
}

@Serializable
private class IngredientOptionDto(
    val id: String,
    val name: String,
    @SerialName("unit_name") val unitName: String? = null,
) {
    fun toModel() = IngredientOption(id, name, unitName)
}

@Serializable
private class BuyerOptionDto(
    val id: String,
    val name: String,
    @SerialName("outlet_name") val outletName: String? = null,
)

@Serializable
private class ReceiptLineDto(
    val name: String,
    val amount: JsonElement,
    val quantity: Int? = null,
    val ingredient: IngredientOptionDto? = null,
    val suggestions: List<IngredientOptionDto> = emptyList(),
)

@Serializable
private class ReceiptReadingDto(
    val store: String? = null,
    @SerialName("bought_on") val boughtOn: String? = null,
    val total: JsonElement? = null,
    val items: List<ReceiptLineDto> = emptyList(),
) {
    fun toModel() = ReceiptReading(
        store = store?.takeIf { it.isNotBlank() },
        boughtOn = boughtOn,
        total = total.toMoneyOrNull(),
        entries = items.map { line ->
            ReceiptLine(line.name, line.amount.toMoney(), line.quantity, line.ingredient?.toModel(), line.suggestions.map { it.toModel() })
        },
    )
}

@Serializable
private class DayStateDto(
    @SerialName("outlet_id") val outletId: String,
    val day: String,
    val deposited: JsonElement,
    val unfinished: Boolean,
) {
    fun toModel() = DayState(outletId, day, deposited.toMoney(), unfinished)
}
