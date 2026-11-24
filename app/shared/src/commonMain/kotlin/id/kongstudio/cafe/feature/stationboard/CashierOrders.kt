package id.kongstudio.cafe.feature.stationboard

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.cashier.PickedExtra
import id.kongstudio.cafe.feature.cashier.PrintableLine
import id.kongstudio.cafe.feature.cashier.PrintableOrder
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement

private const val SessionsPath = "/v2/operational/sessions"
private const val TakeAwayType = "take_away"
internal const val CashierOrderPageSize = 50
internal const val CashierSearchMaxLength = 100

internal enum class CashierCancellationStatus(val code: String) {
    Pending("pending"),
    Approved("approved"),
    Rejected("rejected"),
    ;

    companion object {
        fun of(code: String) = entries.firstOrNull { it.code == code } ?: Pending
    }
}

internal class CashierCancellation(
    val id: String,
    val status: CashierCancellationStatus,
    val requestedById: String,
    val requestedByName: String?,
    val reason: String?,
)

internal class CashierOrderExtra(val name: String, val quantity: Int, val price: Long)

internal class CashierOrderLine(
    val menuItemId: String?,
    val name: String,
    val quantity: Int,
    val unitPrice: Long,
    val subtotal: Long,
    val note: String?,
    val variants: List<String>,
    val extras: List<CashierOrderExtra>,
) {
    val details: List<String> get() = variants + extras.map { it.name }
}

/** Satu pesanan sesi aktif yang dibaca station Kasir, lengkap untuk rincian dan cetak ulang struk. */
internal class CashierOrder(
    val id: String,
    val receipt: String?,
    val businessDay: String,
    val createdAt: String,
    val customerName: String?,
    val tableNo: String?,
    val takeAway: Boolean,
    val note: String?,
    val paymentLabel: String?,
    val cashReceived: Long?,
    val promoName: String?,
    val discount: Long,
    val total: Long,
    val voided: Boolean,
    val served: Boolean,
    val cashierName: String?,
    val cancellation: CashierCancellation?,
    val lines: List<CashierOrderLine>,
    /** Bill yang sudah dikerjakan dapur tetapi belum dibayar; belum masuk omzet sesi. */
    val open: Boolean = false,
    /** Naik tiap bill berubah; pembayar membawa versi yang dilihatnya. */
    val version: Int = 1,
    /** Bill milik sesi kasir yang sedang masuk; hanya pemiliknya yang bisa mengubah atau membayarnya. */
    val mine: Boolean = false,
) {
    val pendingCancel: CashierCancellation? get() = cancellation?.takeIf { it.status == CashierCancellationStatus.Pending }

    /** [categoryOf] membaca kategori menu terbaru dari UUID menu, supaya struk pesanan Bar/Dapur ikut pembagian printer sekarang. */
    fun toPrintable(categoryOf: (String?) -> String?, reprintedAt: Long? = null): PrintableOrder {
        val epoch = isoToEpoch(createdAt) ?: 0L
        return PrintableOrder(
            receiptNumber = receipt,
            takeAway = takeAway,
            customerName = customerName,
            tableNo = tableNo,
            paymentLabel = paymentLabel.orEmpty(),
            lines = lines.map { line ->
                PrintableLine(
                    name = line.name,
                    quantity = line.quantity,
                    unitPrice = line.unitPrice,
                    details = line.details,
                    note = line.note,
                    category = "",
                    categoryId = categoryOf(line.menuItemId),
                    variants = line.variants,
                    extras = line.extras.map { PickedExtra(it.name, it.quantity, it.price) },
                )
            },
            promoName = promoName,
            discount = discount,
            total = total,
            cashReceived = cashReceived,
            change = cashReceived?.let { (it - total).coerceAtLeast(0) } ?: 0,
            cashier = cashierName.orEmpty(),
            dateText = businessDay,
            timeText = DateTimeFormat.stampAt(epoch).time,
            queued = false,
            epochSeconds = epoch,
            noteLabel = note,
            reprintedAt = reprintedAt,
        )
    }
}

internal class CashierOrderPage(val orders: List<CashierOrder>, val nextCursor: String?)

/** Daftar pesanan sesi aktif untuk station Kasir: berhalaman kursor dan dicari ke seluruh isi pesanan oleh server. */
internal class CashierOrderRepository(private val api: AdminApi) {
    suspend fun page(sessionId: String, query: String, cursor: String?): DeviceResult<CashierOrderPage> =
        api.get(
            path = "$SessionsPath/$sessionId/orders/page",
            serializer = OrderPageDto.serializer(),
            query = buildMap<String, Any?> {
                put("limit", CashierOrderPageSize)
                query.trim().takeIf { it.isNotEmpty() }?.let { put("q", it.take(CashierSearchMaxLength)) }
                cursor?.let { put("cursor", it) }
            },
        ).map { dto -> CashierOrderPage(dto.orders.map { it.toModel() }, dto.nextCursor) }

    // Pesanan cabang dari sesi kasir yang sudah ditutup yang menunya masih di stasiun, terlama dulu.
    suspend fun leftBehind(sessionId: String): DeviceResult<List<CashierOrder>> =
        api.get(path = "$SessionsPath/$sessionId/orders/left-behind", serializer = ListSerializer(OrderDto.serializer()))
            .map { list -> list.map { it.toModel() } }
}

@Serializable
private class OrderPageDto(
    val orders: List<OrderDto> = emptyList(),
    @SerialName("next_cursor") val nextCursor: String? = null,
)

@Serializable
internal class OrderDto(
    val id: String,
    @SerialName("business_day") val businessDay: String,
    @SerialName("receipt_number") val receiptNumber: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("customer_name") val customerName: String? = null,
    @SerialName("table_no") val tableNo: String? = null,
    @SerialName("order_type") val orderType: String,
    val note: String? = null,
    @SerialName("payment_method_label") val paymentLabel: String? = null,
    @SerialName("cash_received") val cashReceived: JsonElement? = null,
    @SerialName("promo_name") val promoName: String? = null,
    val discount: JsonElement? = null,
    val total: JsonElement? = null,
    val voided: Boolean = false,
    val served: Boolean = false,
    @SerialName("cashier_name") val cashierName: String? = null,
    val cancellation: CancellationDto? = null,
    val items: List<ItemDto> = emptyList(),
    @SerialName("is_open") val isOpen: Boolean = false,
    val version: Int = 1,
    val mine: Boolean = false,
) {
    fun toModel() = CashierOrder(
        id = id,
        receipt = receiptNumber?.takeIf { it.isNotBlank() },
        businessDay = businessDay,
        createdAt = createdAt,
        customerName = customerName?.takeIf { it.isNotBlank() },
        tableNo = tableNo?.takeIf { it.isNotBlank() },
        takeAway = orderType == TakeAwayType,
        note = note?.takeIf { it.isNotBlank() },
        paymentLabel = paymentLabel?.takeIf { it.isNotBlank() },
        cashReceived = cashReceived.toMoneyOrNull(),
        promoName = promoName?.takeIf { it.isNotBlank() },
        discount = discount.toMoney(),
        total = total.toMoney(),
        voided = voided,
        served = served,
        cashierName = cashierName?.takeIf { it.isNotBlank() },
        cancellation = cancellation?.let {
            CashierCancellation(it.id, CashierCancellationStatus.of(it.status), it.requestedById, it.requestedByName?.takeIf { name -> name.isNotBlank() }, it.reason?.takeIf { text -> text.isNotBlank() })
        },
        lines = items.map { item ->
            CashierOrderLine(
                menuItemId = item.menuItemId,
                name = item.name,
                quantity = item.quantity,
                unitPrice = item.unitPrice.toMoney(),
                subtotal = item.subtotal.toMoney(),
                note = item.note?.takeIf { it.isNotBlank() },
                variants = item.variantNames,
                extras = item.extras.map { CashierOrderExtra(it.name, it.quantity, it.price.toMoney()) },
            )
        },
        open = isOpen,
        version = version,
        mine = mine,
    )
}

@Serializable
internal class CancellationDto(
    val id: String,
    val status: String,
    @SerialName("requested_by_id") val requestedById: String,
    @SerialName("requested_by_name") val requestedByName: String? = null,
    val reason: String? = null,
)

@Serializable
internal class ItemDto(
    @SerialName("menu_item_id") val menuItemId: String? = null,
    val name: String,
    @SerialName("qty") val quantity: Int,
    @SerialName("unit_price") val unitPrice: JsonElement? = null,
    val subtotal: JsonElement? = null,
    val note: String? = null,
    @SerialName("variant_names") val variantNames: List<String> = emptyList(),
    val extras: List<ExtraDto> = emptyList(),
)

@Serializable
internal class ExtraDto(
    val name: String,
    @SerialName("qty") val quantity: Int = 1,
    val price: JsonElement? = null,
)
