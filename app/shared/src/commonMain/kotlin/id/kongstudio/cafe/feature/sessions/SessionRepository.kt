package id.kongstudio.cafe.feature.sessions

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement

internal const val SessionPageSize = 20
internal const val SessionParamFrom = "from"
internal const val SessionParamTo = "to"
private const val SessionsPath = "/v2/operational/sessions"

internal class SessionItem(
    val id: String,
    val code: String?,
    val startedAt: String,
    val endedAt: String?,
    val open: Boolean,
    val openingCash: Long,
    val transactions: Int,
    val canceled: Int,
    val revenue: Long,
    val cashRevenue: Long,
    val nonCashRevenue: Long,
    val spent: Long,
    /** Pengeluaran dari uang laci, dari dana lain, dan pemakaian dana belanja; ketiganya dirinci di halaman sesi. */
    val drawerSpent: Long,
    val otherFundSpent: Long,
    val shoppingFundUsed: Long,
    /** Omzet yang semestinya di tangan: tunai dikurangi belanja laci dan dana belanja. */
    val expectedRevenue: Long,
    /** Omzet yang dihitung kasir saat tutup; null selama berjalan atau bila sesi tidak dihitung per bagian. */
    val actualRevenue: Long?,
    val expectedCash: Long,
    val actualCash: Long?,
    val difference: Long?,
    val note: String?,
)

/** Pendapatan satu metode bayar dalam satu sesi; dua rekening transfer tampil sebagai dua baris. */
internal class MethodTotal(val label: String, val cash: Boolean, val amount: Long, val transactions: Int)

internal class SessionOrderLine(val name: String, val quantity: Int, val options: List<String>)

internal class SessionOrder(
    val id: String,
    val receiptNumber: String?,
    val createdAt: String,
    val paymentLabel: String?,
    val total: Long,
    val voided: Boolean,
    val lines: List<SessionOrderLine>,
)

/** Sesi milik karyawan pemegang tablet di backend v2, termasuk pesanan satu sesi untuk dibaca saja. */
internal class SessionRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest, size: Int = SessionPageSize): DeviceResult<ListPage<SessionItem>> =
        when (
            val result = api.get(
                path = "$SessionsPath/mine",
                serializer = SessionPageDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to size,
                    "start" to request.params[SessionParamFrom],
                    "end" to request.params[SessionParamTo],
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    suspend fun methods(sessionId: String): DeviceResult<List<MethodTotal>> =
        when (val result = api.get(path = "$SessionsPath/$sessionId/methods", serializer = ListSerializer(MethodTotalDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { MethodTotal(it.label, it.cash, it.amount.toMoney(), it.transactions) })
        }

    suspend fun orders(sessionId: String): DeviceResult<List<SessionOrder>> =
        when (val result = api.get(path = "$SessionsPath/$sessionId/orders", serializer = ListSerializer(OrderDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() })
        }
}

@Serializable
private class MethodTotalDto(val label: String, val cash: Boolean = false, val amount: JsonElement? = null, val transactions: Int = 0)

@Serializable
private class SessionPageDto(val items: List<SessionRowDto>, val total: Int)

@Serializable
private class SessionRowDto(
    val id: String,
    @SerialName("shift_code") val code: String? = null,
    @SerialName("opened_at") val startedAt: String,
    @SerialName("closed_at") val endedAt: String? = null,
    val running: Boolean = false,
    @SerialName("opening_cash") val openingCash: JsonElement? = null,
    val transactions: Int = 0,
    @SerialName("voided_transactions") val canceled: Int = 0,
    val revenue: JsonElement? = null,
    @SerialName("cash_revenue") val cashRevenue: JsonElement? = null,
    @SerialName("non_cash_revenue") val nonCashRevenue: JsonElement? = null,
    val expenses: JsonElement? = null,
    @SerialName("drawer_expenses") val drawerExpenses: JsonElement? = null,
    @SerialName("other_fund_expenses") val otherFundExpenses: JsonElement? = null,
    @SerialName("shopping_fund_used") val shoppingFundUsed: JsonElement? = null,
    @SerialName("expected_revenue") val expectedRevenue: JsonElement? = null,
    @SerialName("actual_revenue") val actualRevenue: JsonElement? = null,
    @SerialName("expected_cash") val expectedCash: JsonElement? = null,
    @SerialName("actual_cash") val actualCash: JsonElement? = null,
    val difference: JsonElement? = null,
    val note: String? = null,
) {
    fun toModel() = SessionItem(
        id = id,
        code = code?.takeIf { it.isNotBlank() },
        startedAt = startedAt,
        endedAt = endedAt,
        open = running,
        openingCash = openingCash.toMoney(),
        transactions = transactions,
        canceled = canceled,
        revenue = revenue.toMoney(),
        cashRevenue = cashRevenue.toMoney(),
        nonCashRevenue = nonCashRevenue.toMoney(),
        spent = expenses.toMoney(),
        drawerSpent = drawerExpenses.toMoney(),
        otherFundSpent = otherFundExpenses.toMoney(),
        shoppingFundUsed = shoppingFundUsed.toMoney(),
        expectedRevenue = expectedRevenue.toMoney(),
        actualRevenue = actualRevenue.toMoneyOrNull(),
        expectedCash = expectedCash.toMoney(),
        actualCash = actualCash.toMoneyOrNull(),
        difference = difference.toMoneyOrNull(),
        note = note?.takeIf { it.isNotBlank() },
    )
}

@Serializable
private class OrderDto(
    val id: String,
    @SerialName("receipt_number") val receiptNumber: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("payment_method_label") val paymentLabel: String? = null,
    val total: JsonElement? = null,
    val voided: Boolean = false,
    val items: List<OrderItemDto> = emptyList(),
) {
    fun toModel() = SessionOrder(
        id = id,
        receiptNumber = receiptNumber?.takeIf { it.isNotBlank() },
        createdAt = createdAt,
        paymentLabel = paymentLabel?.takeIf { it.isNotBlank() },
        total = total.toMoney(),
        voided = voided,
        lines = items.map { item -> SessionOrderLine(item.name, item.quantity, item.variantNames + item.extras.map { it.name }) },
    )
}

@Serializable
private class OrderItemDto(
    val name: String,
    @SerialName("qty") val quantity: Int,
    @SerialName("variant_names") val variantNames: List<String> = emptyList(),
    val extras: List<OrderExtraDto> = emptyList(),
)

@Serializable
private class OrderExtraDto(val name: String)
