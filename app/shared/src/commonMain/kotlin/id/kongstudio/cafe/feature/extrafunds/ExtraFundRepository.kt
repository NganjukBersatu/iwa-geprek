package id.kongstudio.cafe.feature.extrafunds

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val ExtraFundTables = setOf("overpayments")

internal const val ExtraFundPageSize = 20

/** Satu kelebihan bayar non-tunai: uang masuk ke rekening lebih besar dari total pesanan. */
internal class ExtraFund(
    val id: String,
    val receipt: String?,
    val at: String,
    val cashier: String,
    val method: String,
    val orderTotal: Long,
    val received: Long,
    val extra: Long,
    val voided: Boolean,
    val purchase: String,
)

internal data class ExtraFundTotals(val count: Int = 0, val total: Long = 0)

internal class ExtraFundRepository(private val api: AdminApi) {
    private val _totals = MutableStateFlow(ExtraFundTotals())
    val totals: StateFlow<ExtraFundTotals> = _totals.asStateFlow()

    suspend fun list(request: PageRequest): DeviceResult<ListPage<ExtraFund>> =
        when (
            val result = api.get(
                path = "/v2/operational/overpayments",
                serializer = ExtraFundReportDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to ExtraFundPageSize,
                    "sort" to request.sort,
                    "start" to request.params["from"],
                    "end" to request.params["to"],
                    "user_id" to request.params[ListParam.UserId],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> {
                _totals.value = ExtraFundTotals(result.value.count, result.value.total.toMoney())
                DeviceResult.Ok(ListPage(result.value.rows.map { it.toModel() }, result.value.count))
            }
        }
}

@Serializable
private class ExtraFundReportDto(
    val count: Int = 0,
    @SerialName("total_amount") val total: JsonElement? = null,
    val rows: List<ExtraFundDto> = emptyList(),
)

@Serializable
private class ExtraFundDto(
    val id: String,
    @SerialName("receipt_number") val receipt: String? = null,
    @SerialName("recorded_at") val at: String,
    val cashier: String = "",
    @SerialName("method_label") val method: String = "",
    @SerialName("order_total") val orderTotal: JsonElement? = null,
    val received: JsonElement? = null,
    @SerialName("amount") val extra: JsonElement? = null,
    val voided: Boolean = false,
    @SerialName("purchases") val purchase: String = "",
) {
    fun toModel() = ExtraFund(
        id = id,
        receipt = receipt?.takeIf { it.isNotBlank() },
        at = at,
        cashier = cashier,
        method = method,
        orderTotal = orderTotal.toMoney(),
        received = received.toMoney(),
        extra = extra.toMoney(),
        voided = voided,
        purchase = purchase,
    )
}
