package id.kongstudio.cafe.feature.resalestock

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

internal const val ResalePageSize = 30
private const val ResalePath = "/v2/operational/resale-stock"

// Tabel yang perubahannya memuat ulang daftar lewat /v2/live: stok barang dan kartu stoknya.
internal val ResaleTables = setOf("stock_items", "stock_cards")

/** Penyaring daftar: stok sekarang, atau riwayat satu jenis catatan; kodenya dipakai server. */
internal const val FilterStock = "stock"
internal const val FilterReceipt = "receipt"
internal const val FilterAdjustment = "adjustment"

internal enum class ResaleStatus(val code: String) {
    Out("habis"),
    Low("menipis"),
    Safe("aman"),
    ;

    companion object {
        /** Status yang tidak dikenal dianggap aman supaya penanda palsu tidak muncul. */
        fun of(code: String): ResaleStatus = entries.firstOrNull { it.code == code } ?: Safe
    }
}

internal class ResaleItem(val menuItemId: String, val name: String, val unit: String?, val stock: String, val status: ResaleStatus)

internal class ResaleMovement(
    val id: String,
    val menuItemName: String,
    val unit: String?,
    val qty: String,
    val note: String?,
    val userName: String?,
    val createdAt: String,
)

/** Satu baris daftar: barang pada penyaring stok, atau catatan pada penyaring riwayat. */
internal sealed interface ResaleRow {
    class Item(val value: ResaleItem) : ResaleRow

    class Movement(val value: ResaleMovement) : ResaleRow
}

internal class ResaleCountResult(val counted: Int, val adjusted: Int)

internal class ResaleStockRepository(private val api: AdminApi) {
    suspend fun rows(request: PageRequest): DeviceResult<ListPage<ResaleRow>> =
        if (request.filter == FilterStock || request.filter.isEmpty()) items(request) else movements(request)

    private suspend fun items(request: PageRequest): DeviceResult<ListPage<ResaleRow>> =
        when (
            val result = api.get(
                path = "$ResalePath/items",
                serializer = ItemPageDto.serializer(),
                query = mapOf("page" to request.page + 1, "size" to ResalePageSize, "search" to request.query, "sort" to request.sort),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { ResaleRow.Item(it.toModel()) }, result.value.total))
        }

    private suspend fun movements(request: PageRequest): DeviceResult<ListPage<ResaleRow>> =
        when (
            val result = api.get(
                path = "$ResalePath/movements",
                serializer = MovementPageDto.serializer(),
                query = mapOf(
                    "kind" to request.filter,
                    "page" to request.page + 1,
                    "size" to ResalePageSize,
                    "sort" to request.sort,
                    "start" to request.params[ListParam.From],
                    "end" to request.params[ListParam.To],
                    "user_id" to request.params[ListParam.UserId],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { ResaleRow.Movement(it.toModel()) }, result.value.total))
        }

    suspend fun receive(menuItemId: String, qty: String, note: String): DeviceResult<Unit> =
        write("receipts", buildJsonObject {
            put("menu_item_id", menuItemId)
            put("qty", qty)
            putText("note", note)
        })

    /** [qty] sudah bertanda: positif menambah, negatif mengurangi. */
    suspend fun adjust(menuItemId: String, qty: String, note: String): DeviceResult<Unit> =
        write("adjustments", buildJsonObject {
            put("menu_item_id", menuItemId)
            put("qty", qty)
            put("note", note.trim())
        })

    /** [lines] berisi pasangan id barang dan jumlah fisik yang sudah dirapikan. */
    suspend fun closeCount(note: String, lines: List<Pair<String, String>>): DeviceResult<ResaleCountResult> =
        when (
            val result = api.send(
                method = HttpMethod.Post,
                path = "$ResalePath/counts",
                body = buildJsonObject {
                    putText("note", note)
                    put("lines", buildJsonArray {
                        lines.forEach { (id, counted) ->
                            add(buildJsonObject {
                                put("menu_item_id", id)
                                put("counted", counted)
                            })
                        }
                    })
                },
                serializer = CountDto.serializer(),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ResaleCountResult(result.value.counted, result.value.adjusted))
        }

    private suspend fun write(route: String, body: JsonElement): DeviceResult<Unit> =
        when (val result = api.send(method = HttpMethod.Post, path = "$ResalePath/$route", body = body, serializer = MovementDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(Unit)
        }
}

@Serializable
private class ItemDto(
    @SerialName("menu_item_id") val menuItemId: String,
    val name: String,
    val unit: String? = null,
    val stock: String = "0",
    val status: String = "aman",
) {
    fun toModel() = ResaleItem(menuItemId, name, unit, stock, ResaleStatus.of(status))
}

@Serializable
private class ItemPageDto(val items: List<ItemDto>, val total: Int)

@Serializable
private class MovementDto(
    val id: String,
    @SerialName("menu_item_name") val menuItemName: String = "",
    val unit: String? = null,
    val qty: String = "0",
    val note: String? = null,
    @SerialName("user_name") val userName: String? = null,
    @SerialName("created_at") val createdAt: String = "",
) {
    fun toModel() = ResaleMovement(id, menuItemName, unit, qty, note, userName, createdAt)
}

@Serializable
private class MovementPageDto(val items: List<MovementDto>, val total: Int)

@Serializable
private class CountDto(val counted: Int = 0, val adjusted: Int = 0)
