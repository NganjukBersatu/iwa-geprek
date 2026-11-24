package id.kongstudio.cafe.feature.openbill

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.cashier.CartEntry
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import id.kongstudio.cafe.feature.stationboard.CashierOrder
import id.kongstudio.cafe.feature.stationboard.OrderDto
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

private const val OrdersPath = "/v2/operational/orders"

/** Harga bill dengan promo yang sedang dilihat kasir, dihitung server; tablet tidak menghitung potongan sendiri. */
internal class BillQuote(val subtotal: Long, val discount: Long, val total: Long, val promoName: String?)

/** Bill yang sudah diterima dapur tetapi belum dibayar: daftar, tambah menu, bayar, dan batal; semuanya butuh koneksi. */
internal class OpenBillRepository(private val api: AdminApi) {
    suspend fun bills(): DeviceResult<List<CashierOrder>> =
        api.get(path = "$OrdersPath/open", serializer = ListSerializer(OrderDto.serializer())).map { list -> list.map { it.toModel() } }

    suspend fun addMenus(bill: CashierOrder, entries: List<CartEntry>): DeviceResult<CashierOrder> =
        api.send(
            method = HttpMethod.Post,
            path = "$OrdersPath/${bill.id}/lines",
            body = buildJsonObject {
                put("version", bill.version)
                put(
                    "items",
                    buildJsonArray {
                        entries.forEach { entry ->
                            add(
                                buildJsonObject {
                                    put("menu_item_id", entry.menuId)
                                    put("qty", entry.quantity)
                                    entry.note?.let { put("note", it) }
                                    put("variant_ids", buildJsonArray { entry.variantIds.forEach { add(kotlinx.serialization.json.JsonPrimitive(it)) } })
                                    put(
                                        "extras",
                                        buildJsonArray {
                                            entry.extras.forEach { (id, count) ->
                                                add(buildJsonObject { put("extra_id", id); put("qty", count) })
                                            }
                                        },
                                    )
                                },
                            )
                        }
                    },
                )
            },
            serializer = OrderDto.serializer(),
        ).map { it.toModel() }

    suspend fun quote(bill: CashierOrder, promoId: String?): DeviceResult<BillQuote> =
        api.send(
            method = HttpMethod.Post,
            path = "$OrdersPath/${bill.id}/quote",
            body = buildJsonObject { promoId?.let { put("promo_id", it) } },
            serializer = QuoteDto.serializer(),
        ).map { BillQuote(it.subtotal.toMoney(), it.discount.toMoney(), it.total.toMoney(), it.promoName) }

    /** [settleKey] dibuat sekali per pembayaran: kirim ulang dengan kunci sama tidak membayar dua kali. */
    suspend fun settle(bill: CashierOrder, paymentCode: String, cashReceived: Long?, promoId: String?, settleKey: String): DeviceResult<CashierOrder> =
        api.send(
            method = HttpMethod.Post,
            path = "$OrdersPath/${bill.id}/settle",
            body = buildJsonObject {
                put("version", bill.version)
                put("payment_method", paymentCode)
                cashReceived?.let { put("cash_received", it) }
                promoId?.let { put("promo_id", it) }
                put("settle_key", settleKey)
            },
            serializer = OrderDto.serializer(),
        ).map { it.toModel() }

    suspend fun cancel(bill: CashierOrder, reason: String): DeviceResult<CashierOrder> =
        api.send(
            method = HttpMethod.Post,
            path = "$OrdersPath/${bill.id}/cancel",
            body = buildJsonObject { reason.trim().takeIf { it.isNotEmpty() }?.let { put("reason", it) } },
            serializer = OrderDto.serializer(),
        ).map { it.toModel() }
}

@Serializable
private class QuoteDto(
    val subtotal: JsonElement? = null,
    val discount: JsonElement? = null,
    val total: JsonElement? = null,
    @SerialName("promo_name") val promoName: String? = null,
)
