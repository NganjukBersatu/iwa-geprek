package id.kongstudio.cafe.feature.sessions

import id.kongstudio.cafe.feature.admin.AdminJson
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import io.ktor.client.HttpClient
import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.header
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.content.TextContent
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

private const val SessionsPath = "/v2/operational/sessions"
private const val TakeAwayType = "take_away"
internal const val DeviceHeader = "X-Device"

/** [businessDay] adalah hari bisnis sesi, "YYYY-MM-DD": hari semua penjualan, pengeluaran, promo, dan nomor nota sesi ini. */
internal class ActiveSession(val id: String, val openingCash: Long, val businessDay: String)

/** Pesanan tertinggal dari sesi lain yang sudah ditutup, cukup untuk modal pengingat. */
internal class LeftBehindOrder(
    val id: String,
    val receipt: String?,
    val tableNo: String?,
    val takeAway: Boolean,
    val customerName: String?,
    val cashierName: String?,
    val items: String,
)

/** Angka sebelum tutup; [threeParts] ditentukan saat sesi dibuka, dan saat itu tutup meminta modal, belanja, dan omzet terpisah. */
internal class SessionRecap(
    val expectedCash: Long,
    val threeParts: Boolean,
    val plannedFloat: Long?,
    val plannedShopping: Long?,
    val expectedRevenue: Long,
    // Pesanan sesi ini yang masih ada di papan stasiun; hanya peringatan, tidak menahan tutup sesi.
    val stationOpenOrders: Int,
)

/** Uang yang dihitung saat tutup: satu angka untuk sesi biasa, tiga bagian untuk sesi beruang belanja. */
internal sealed interface CountedCash {
    class Single(val actualCash: Long) : CountedCash

    class ThreeParts(val actualFloat: Long, val actualShopping: Long, val actualRevenue: Long) : CountedCash
}

/** Buka dan tutup sesi kas di backend v2: buka dikenali dari token perangkat kasir, sedangkan tutup, sesi aktif, dan rekap atas nama karyawan. */
internal class SessionControlRepository(
    private val client: HttpClient,
    private val baseUrl: String,
    private val token: String,
    private val deviceToken: String,
) {
    /** Karyawan tanpa sesi aktif dijawab null oleh server; itu keadaan normal, bukan galat. */
    suspend fun active(): DeviceResult<ActiveSession?> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Get,
        path = "$SessionsPath/active",
        bearer = token,
        parse = { response ->
            val raw = response.bodyAsText()
            if (raw.isBlank() || raw == "null") null else AdminJson.decodeFromString(SessionDto.serializer(), raw).toModel()
        },
    )

    suspend fun open(openingCash: Long): DeviceResult<ActiveSession> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Post,
        path = SessionsPath,
        bearer = token,
        configure = {
            header(DeviceHeader, deviceToken)
            setJson(buildJsonObject { put("opening_cash", openingCash) })
        },
        parse = { AdminJson.decodeFromString(SessionDto.serializer(), it.bodyAsText()).toModel() },
    )

    suspend fun recap(sessionId: String): DeviceResult<SessionRecap> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Get,
        path = "$SessionsPath/$sessionId/recap",
        bearer = token,
        parse = { AdminJson.decodeFromString(RecapDto.serializer(), it.bodyAsText()).toModel() },
    )

    suspend fun close(sessionId: String, counted: CountedCash, note: String): DeviceResult<Unit> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Post,
        path = "$SessionsPath/$sessionId/close",
        bearer = token,
        configure = {
            setJson(
                buildJsonObject {
                    when (counted) {
                        is CountedCash.Single -> put("actual_cash", counted.actualCash)
                        is CountedCash.ThreeParts -> {
                            put("actual_float", counted.actualFloat)
                            put("actual_shopping", counted.actualShopping)
                            put("actual_revenue", counted.actualRevenue)
                        }
                    }
                    putText("note", note)
                },
            )
        },
        parse = { },
    )

    // Pesanan cabang dari sesi kasir yang sudah ditutup yang menunya masih di stasiun.
    suspend fun leftBehind(sessionId: String): DeviceResult<List<LeftBehindOrder>> = deviceCall(
        client = client,
        baseUrl = baseUrl,
        method = HttpMethod.Get,
        path = "$SessionsPath/$sessionId/orders/left-behind",
        bearer = token,
        parse = { response -> AdminJson.decodeFromString(ListSerializer(LeftBehindDto.serializer()), response.bodyAsText()).map { it.toModel() } },
    )

    private fun HttpRequestBuilder.setJson(body: JsonElement) {
        setBody(TextContent(body.toString(), ContentType.Application.Json))
    }
}

@Serializable
private class SessionDto(
    val id: String,
    @SerialName("business_day") val businessDay: String,
    @SerialName("opening_cash") val openingCash: JsonElement? = null,
    @SerialName("three_parts") val threeParts: Boolean = false,
    @SerialName("planned_float") val plannedFloat: JsonElement? = null,
    @SerialName("planned_shopping") val plannedShopping: JsonElement? = null,
) {
    fun toModel() = ActiveSession(id, openingCash.toMoney(), businessDay)
}

@Serializable
private class LeftBehindItemDto(val name: String, val qty: Int = 0)

@Serializable
private class LeftBehindDto(
    val id: String,
    @SerialName("receipt_number") val receiptNumber: String? = null,
    @SerialName("table_no") val tableNo: String? = null,
    @SerialName("order_type") val orderType: String = "",
    @SerialName("customer_name") val customerName: String? = null,
    @SerialName("cashier_name") val cashierName: String? = null,
    val items: List<LeftBehindItemDto> = emptyList(),
) {
    fun toModel() = LeftBehindOrder(
        id = id,
        receipt = receiptNumber?.takeIf { it.isNotBlank() },
        tableNo = tableNo?.takeIf { it.isNotBlank() },
        takeAway = orderType == TakeAwayType,
        customerName = customerName?.takeIf { it.isNotBlank() },
        cashierName = cashierName?.takeIf { it.isNotBlank() },
        items = items.joinToString(", ") { "${it.qty}x ${it.name}" },
    )
}

@Serializable
private class RecapDto(
    val session: SessionDto,
    @SerialName("expected_cash") val expectedCash: JsonElement? = null,
    @SerialName("expected_revenue") val expectedRevenue: JsonElement? = null,
    @SerialName("station_open_orders") val stationOpenOrders: Int = 0,
) {
    fun toModel() = SessionRecap(
        expectedCash = expectedCash.toMoney(),
        threeParts = session.threeParts,
        plannedFloat = session.plannedFloat.toMoneyOrNull(),
        plannedShopping = session.plannedShopping.toMoneyOrNull(),
        expectedRevenue = expectedRevenue.toMoney(),
        stationOpenOrders = stationOpenOrders,
    )
}
