package id.kongstudio.cafe.feature.cashier

import id.kongstudio.cafe.core.failure.isOffline
import id.kongstudio.cafe.core.format.hundredthsOf
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.core.time.ShiftDay
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import id.kongstudio.cafe.feature.ordersync.OrdersPath
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrintPlanDto
import id.kongstudio.cafe.feature.printer.PrintPlanPath
import id.kongstudio.cafe.feature.sessions.DeviceHeader
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.offline.newClientId
import id.kongstudio.cafe.offline.userIdOf
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.timeout
import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.header
import io.ktor.client.request.parameter
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull

private const val CashierPath = "/v2/operational/cashier"
private const val ActiveSessionPath = "/v2/operational/sessions/active"
private const val CustomerSuggestionsPath = "/v2/operational/customers/suggestions"
private const val OrderNotesPath = "/v2/operational/order-notes"
private const val UncategorizedLabel = "Lainnya"
private const val BestsellerLimit = 10
// Kunci cache v2: isi lama berbentuk backend lama dan tidak terbaca bentuk baru.
private const val BestsellerCacheKey = "cashier.v2.bestseller"
private const val MenuCacheKey = "cashier.v2.menu"
private const val MethodsCacheKey = "cashier.v2.methods"
private const val ShiftCacheKey = "cashier.v2.shift-day"
private const val ShopCacheKey = "cashier.v2.shop"
private const val PrintPlanCacheKey = "cashier.v2.print-plan"
private const val VisitorsCacheKey = "cashier.v2.visitors"
private const val PromosCacheKey = "cashier.v2.promos"
private const val OrderNotesCacheKey = "cashier.v2.order-notes"
private const val SubmitConnectMillis = 8_000L
private const val SubmitRequestMillis = 20_000L

private val CacheJson = Json { ignoreUnknownKeys = true }

/** Satu metode bayar cabang tablet: [icon] nama ikon Tabler, [missing] syarat yang belum disetel di web (kosong berarti siap), serta [imageUrl] dan [note] untuk pelanggan. */
internal class PaymentMethod(
    val code: String,
    val label: String,
    val needsChange: Boolean,
    val icon: String = "",
    val missing: List<String> = emptyList(),
    val imageUrl: String? = null,
    val note: String = "",
) {
    val ready: Boolean get() = missing.isEmpty()
}

/** Satu jenis pengunjung; [asksGender] membuat kasir juga memilih gender pemesan. */
internal class VisitorKind(val id: String, val name: String, val asksGender: Boolean)

internal class VisitorGender(val id: String, val name: String)

/** Pilihan pengunjung yang aktif di cabang tablet; keduanya boleh kosong karena pencatatannya opsional. */
internal class VisitorChoices(val categories: List<VisitorKind> = emptyList(), val genders: List<VisitorGender> = emptyList())

/** Pelanggan terdaftar yang cocok dengan ketikan kasir; [visits] jumlah kunjungannya. */
internal class CustomerSuggestion(val id: String, val name: String, val contact: String?, val visits: Int)

/** Satu pilihan catatan untuk seluruh pesanan; daftarnya sama untuk semua cabang. */
internal class OrderNote(val id: String, val name: String)

/** [queued] true bila pesanan baru tersimpan di tablet dan akan dikirim ke server saat tersambung. */
internal class PlacedOrder(val receiptNumber: String?, val total: Long, val change: Long, val queued: Boolean = false)

/** Satu pesanan siap kirim; harga dihitung ulang server, klien hanya mengirim pilihannya. */
internal class OrderDraft(
    val takeAway: Boolean,
    val customerName: String?,
    val tableNo: String?,
    val paymentCode: String,
    val cashReceived: Long?,
    val entries: List<CartEntry>,
    val visitorCategoryId: String? = null,
    val visitorGenderId: String? = null,
    val promoId: String? = null,
    val customerId: String? = null,
    val noteId: String? = null,
    /** Teks catatan yang dilihat kasir, dipakai server bila catatannya terhapus sebelum pesanan sampai. */
    val noteLabel: String? = null,
    /** Bill: dikerjakan dapur sekarang, dibayar belakangan; metode dan promo dipilih saat membayar. */
    val openBill: Boolean = false,
)

/** Panggilan kasir atas nama karyawan yang memindai QR ([token]) dari tablet kasir ([deviceToken]); cabangnya cabang tablet. */
internal class CashierRepository(
    private val client: HttpClient,
    private val baseUrl: String,
    private val token: String,
    private val deviceToken: String,
    private val store: OfflineStore,
) {
    private val userId = userIdOf(token)

    private fun HttpRequestBuilder.fromTablet() {
        header(DeviceHeader, deviceToken)
    }

    /** Hasil baca terakhir milik karyawan ini; dipakai hanya bila server tidak terjangkau. */
    private suspend fun <T> cachedOr(key: String, failed: DeviceResult.Failed, decode: (String) -> T): DeviceResult<T> {
        if (!failed.failure.isOffline) return failed
        val body = userId?.let { runCatching { store.getCache("$it:$key") }.getOrNull() }?.body ?: return failed
        return runCatching<DeviceResult<T>> { DeviceResult.Ok(decode(body)) }.getOrElse { failed }
    }

    private suspend fun remember(key: String, body: String) {
        val owner = userId ?: return
        runCatching { store.putCache("$owner:$key", body, ServerClock.nowEpochSeconds()) }
    }

    suspend fun menu(): DeviceResult<List<CashierItem>> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/menu",
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ListSerializer(MenuItemDto.serializer()), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(MenuCacheKey, result) { raw ->
                CacheJson.decodeFromString(ListSerializer(MenuItemDto.serializer()), raw).map { it.toModel() }
            }
            is DeviceResult.Ok -> {
                remember(MenuCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.map { it.toModel() })
            }
        }
    }

    /** Id menu terlaris dari server; hanya urutannya yang dipakai, isi menunya tetap dari [menu]. */
    suspend fun bestsellerIds(): DeviceResult<List<String>> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/best-sellers",
            bearer = token,
            configure = {
                fromTablet()
                parameter("limit", BestsellerLimit)
            },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ListSerializer(String.serializer()), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(BestsellerCacheKey, result) { raw ->
                CacheJson.decodeFromString(ListSerializer(String.serializer()), raw)
            }
            is DeviceResult.Ok -> {
                remember(BestsellerCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second)
            }
        }
    }

    /** Karyawan tanpa sesi aktif dijawab null server; itu keadaan normal, bukan galat. */
    suspend fun activeShift(): DeviceResult<ShiftDay> {
        val resolved = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = ActiveSessionPath,
            bearer = token,
            parse = { response -> response.bodyAsText().let { raw -> raw to shiftDayOf(raw) } },
        )
        return when (resolved) {
            is DeviceResult.Ok -> {
                remember(ShiftCacheKey, resolved.value.first)
                DeviceResult.Ok(resolved.value.second)
            }
            is DeviceResult.Failed -> cachedOr(ShiftCacheKey, resolved) { shiftDayOf(it) }
        }
    }

    private fun shiftDayOf(raw: String): ShiftDay =
        if (raw.isBlank() || raw == "null") ShiftDay.None else ShiftDay.Running(CacheJson.decodeFromString(ActiveShiftDto.serializer(), raw).businessDay)

    suspend fun paymentMethods(): DeviceResult<List<PaymentMethod>> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/payment-methods",
            bearer = token,
            configure = {
                fromTablet()
                // Yang belum lengkap ikut dikirim supaya tampil "Tidak tersedia", sama seperti kasir web.
                parameter("with_unready", true)
            },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ListSerializer(PaymentMethodDto.serializer()), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(MethodsCacheKey, result) { raw ->
                CacheJson.decodeFromString(ListSerializer(PaymentMethodDto.serializer()), raw).toMethods()
            }
            is DeviceResult.Ok -> {
                remember(MethodsCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.toMethods())
            }
        }
    }

    /** Identitas kafe untuk kepala struk; disimpan agar struk tetap bisa dicetak saat offline. */
    suspend fun shopInfo(): DeviceResult<ShopInfo> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/shop",
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ShopDto.serializer(), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(ShopCacheKey, result) { raw ->
                CacheJson.decodeFromString(ShopDto.serializer(), raw).toModel()
            }
            is DeviceResult.Ok -> {
                remember(ShopCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.toModel())
            }
        }
    }

    /** Rencana cetak tablet ini (struk pembayaran dan printer per stasiun); disimpan supaya struk tetap terbagi saat offline. */
    suspend fun printPlan(): DeviceResult<PrintPlan> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = PrintPlanPath,
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(PrintPlanDto.serializer(), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(PrintPlanCacheKey, result) { raw ->
                CacheJson.decodeFromString(PrintPlanDto.serializer(), raw).toModel()
            }
            is DeviceResult.Ok -> {
                remember(PrintPlanCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.toModel())
            }
        }
    }

    /** Pilihan pengunjung; disimpan supaya tetap bisa dipilih saat offline. */
    suspend fun visitorChoices(): DeviceResult<VisitorChoices> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/visitors",
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(VisitorChoicesDto.serializer(), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(VisitorsCacheKey, result) { raw ->
                CacheJson.decodeFromString(VisitorChoicesDto.serializer(), raw).toModel()
            }
            is DeviceResult.Ok -> {
                remember(VisitorsCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.toModel())
            }
        }
    }

    /** Promo yang belum berakhir, dalam urutan server; disimpan supaya potongan tetap sama saat offline. */
    suspend fun promos(): DeviceResult<List<CashierPromo>> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = "$CashierPath/promos",
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ListSerializer(PromoDto.serializer()), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(PromosCacheKey, result) { raw ->
                CacheJson.decodeFromString(ListSerializer(PromoDto.serializer()), raw).map { it.toModel() }
            }
            is DeviceResult.Ok -> {
                remember(PromosCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.map { it.toModel() })
            }
        }
    }

    /** Saran pelanggan untuk nama atau nomor HP yang diketik; tidak disimpan, karena tiap ketikan menanyakan hal baru. */
    suspend fun customerSuggestions(query: String): DeviceResult<List<CustomerSuggestion>> =
        deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = CustomerSuggestionsPath,
            bearer = token,
            configure = {
                fromTablet()
                parameter("q", query)
            },
            parse = { response -> response.body<List<CustomerSuggestionDto>>().map { it.toModel() } },
        )

    /** Pilihan catatan pesanan; disimpan supaya tetap bisa dipilih saat offline. */
    suspend fun orderNotes(): DeviceResult<List<OrderNote>> {
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Get,
            path = OrderNotesPath,
            bearer = token,
            configure = { fromTablet() },
            parse = { response ->
                val raw = response.bodyAsText()
                raw to CacheJson.decodeFromString(ListSerializer(OrderNoteDto.serializer()), raw)
            },
        )
        return when (result) {
            is DeviceResult.Failed -> cachedOr(OrderNotesCacheKey, result) { raw ->
                CacheJson.decodeFromString(ListSerializer(OrderNoteDto.serializer()), raw).map { it.toModel() }
            }
            is DeviceResult.Ok -> {
                remember(OrderNotesCacheKey, result.value.first)
                DeviceResult.Ok(result.value.second.map { it.toModel() })
            }
        }
    }

    /** Menambah pilihan catatan; nama yang sudah ada dijawab server dengan pilihan yang sama. */
    suspend fun addOrderNote(name: String): DeviceResult<OrderNote> =
        deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Post,
            path = OrderNotesPath,
            bearer = token,
            configure = {
                fromTablet()
                contentType(ContentType.Application.Json)
                setBody(OrderNoteRequestDto(name))
            },
            parse = { it.body<OrderNoteDto>().toModel() },
        )

    /** Server sudah menyaring yang aktif, dalam urutan cabang. */
    private fun List<PaymentMethodDto>.toMethods() =
        map { PaymentMethod(it.code, it.label, it.needsChange, it.icon, it.missing, it.imageUrl, it.note) }

    /** Mengirim pesanan; bila server tidak terjangkau, pesanan disimpan di tablet dengan kunci idempoten dan dikirim nanti, dan harga tetap dihitung ulang server. */
    /** Nomor nota direbut sebelum bayar agar tiket dapur/bar dan struk menyebut nomor yang sama. */
    suspend fun takeReceiptNumber(): DeviceResult<String> =
        deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Post,
            path = "$OrdersPath/receipt-number",
            bearer = token,
            configure = { fromTablet() },
            parse = { it.body<ReceiptNumberDto>().number },
        )

    /** [receipt] nomor yang sudah direbut saat layar bayar dibuka; null berarti direbut sekarang. */
    @OptIn(ExperimentalTime::class)
    suspend fun submit(draft: OrderDraft, localTotal: Long, receipt: String? = null): DeviceResult<PlacedOrder> {
        val clientId = newClientId()
        val createdAt = Instant.fromEpochSeconds(ServerClock.nowEpochSeconds())
        // Gagal merebut di sini tidak menahan penjualan: server memberi nomor sendiri saat pesanan diterima.
        val receipt = receipt ?: (takeReceiptNumber() as? DeviceResult.Ok)?.value

        val request = OrderRequestDto(
            orderType = if (draft.takeAway) TakeAwayCode else "free_table",
            customerName = draft.customerName,
            tableNo = draft.tableNo,
            paymentMethod = draft.paymentCode.takeIf { !draft.openBill },
            cashReceived = draft.cashReceived.takeIf { !draft.openBill },
            receiptNumber = receipt,
            openBill = draft.openBill,
            clientId = clientId,
            visitorCategoryId = draft.visitorCategoryId,
            visitorGenderId = draft.visitorGenderId,
            promoId = draft.promoId,
            customerId = draft.customerId,
            noteId = draft.noteId,
            noteLabel = draft.noteLabel,
            items = draft.entries.map { entry ->
                OrderItemRequestDto(
                    menuItemId = entry.menuId,
                    quantity = entry.quantity,
                    note = entry.note,
                    variantIds = entry.variantIds,
                    extras = entry.extras.map { (id, count) -> ExtraRequestDto(id, count) },
                )
            },
        )
        val result = deviceCall(
            client = client,
            baseUrl = baseUrl,
            method = HttpMethod.Post,
            path = OrdersPath,
            bearer = token,
            configure = {
                fromTablet()
                contentType(ContentType.Application.Json)
                setBody(request)
                timeout {
                    connectTimeoutMillis = SubmitConnectMillis
                    requestTimeoutMillis = SubmitRequestMillis
                }
            },
            parse = { response ->
                val dto = response.body<OrderResponseDto>()
                val total = dto.total.toMoney()
                val received = dto.cashReceived?.toMoney() ?: total
                PlacedOrder(dto.receiptNumber, total, (received - total).coerceAtLeast(0))
            },
        )
        // Bill tidak pernah masuk antrean offline: urutan tambah, bayar, dan batal bergantung pada keadaan terkini di server.
        if (draft.openBill || result !is DeviceResult.Failed || !result.failure.isOffline) return result

        // Server tidak terjangkau: simpan, jangan hilangkan.
        val owner = userId ?: return result
        val queuedPayload = CacheJson.encodeToString(
            OrderRequestDto.serializer(),
            request.copy(createdAt = createdAt.toString()),
        )
        val saved = runCatching {
            store.enqueue(
                clientId = clientId,
                userId = owner,
                payload = queuedPayload,
                createdEpoch = createdAt.epochSeconds,
                total = localTotal,
                itemCount = draft.entries.sumOf { it.quantity },
            )
        }
        if (saved.isFailure) return result
        val received = draft.cashReceived ?: localTotal
        return DeviceResult.Ok(
            PlacedOrder(receipt, localTotal, (received - localTotal).coerceAtLeast(0), queued = true),
        )
    }
}

/** Satu baris menu pesanan tertunda, masih berupa UUID; nama dicari dari katalog kasir saat ditampilkan. */
internal class PendingLine(
    val menuId: String,
    val quantity: Int,
    val note: String?,
    val variantIds: List<String>,
    val extras: List<Pair<String, Int>>,
)

/** Isi pesanan tertunda seperti yang akan dikirim ke server, untuk halaman Mode Offline. */
internal class PendingOrderView(
    val takeAway: Boolean,
    val customerName: String?,
    val tableNo: String?,
    val paymentCode: String,
    val cashReceived: Long?,
    val receiptNumber: String?,
    val noteLabel: String?,
    val lines: List<PendingLine>,
)

private const val TakeAwayCode = "take_away"

/** Membaca isi antrean; null bila tersimpan dengan bentuk yang tidak dikenali lagi, sehingga halaman hanya menampilkan ringkasannya. */
internal fun pendingOrderView(payload: String): PendingOrderView? {
    val dto = runCatching { CacheJson.decodeFromString(OrderRequestDto.serializer(), payload) }.getOrNull() ?: return null
    return PendingOrderView(
        takeAway = dto.orderType == TakeAwayCode,
        customerName = dto.customerName,
        tableNo = dto.tableNo,
        paymentCode = dto.paymentMethod.orEmpty(),
        cashReceived = dto.cashReceived,
        receiptNumber = dto.receiptNumber,
        noteLabel = dto.noteLabel,
        lines = dto.items.map { item -> PendingLine(item.menuItemId, item.quantity, item.note, item.variantIds, item.extras.map { it.id to it.quantity }) },
    )
}

@Serializable
private class ShopDto(
    val name: String = "",
    val address: String = "",
    val phone: String = "",
    @SerialName("receipt_greeting") val thanks: String = "",
    @SerialName("has_wifi") val hasWifi: Boolean = false,
    @SerialName("wifi_password") val wifiPassword: String = "",
    @SerialName("complaint_number") val complaintNumber: String = "",
    @SerialName("social_handles") val socialHandles: List<String> = emptyList(),
) {
    fun toModel() = ShopInfo(name, address, phone, thanks, hasWifi, wifiPassword, complaintNumber, socialHandles)
}

@Serializable
private class PromoDto(
    val id: String,
    val name: String,
    val kind: String,
    @SerialName("discount_type") val discountType: String,
    val value: JsonElement,
    @SerialName("product_ids") val productIds: List<String> = emptyList(),
    @SerialName("minimum_spend") val minimumSpend: JsonElement? = null,
    val activation: String,
    @SerialName("starts_on") val startsOn: String,
    @SerialName("ends_on") val endsOn: String,
) {
    fun toModel() = CashierPromo(
        id = id,
        name = name,
        kind = kind,
        discountType = discountType,
        valueHundredths = (value as? JsonPrimitive)?.contentOrNull?.let(::hundredthsOf) ?: 0L,
        productIds = productIds.toSet(),
        minimumSpend = minimumSpend?.takeUnless { it is JsonNull }?.toMoney(),
        activation = activation,
        startsOn = startsOn,
        endsOn = endsOn,
    )
}

@Serializable
private class MenuItemDto(
    val id: String,
    val name: String,
    val price: JsonElement,
    @SerialName("category_id") val categoryId: String? = null,
    @SerialName("category_name") val category: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("is_available") val available: Boolean = true,
    @SerialName("ready_to_sell") val ready: Boolean = true,
    @SerialName("missing_ingredients") val missingIngredients: List<String> = emptyList(),
    @SerialName("variant_groups") val variantGroups: List<VariantGroupDto> = emptyList(),
    val extras: List<ExtraDto> = emptyList(),
) {
    fun toModel() = CashierItem(
        id = id,
        name = name,
        category = category?.takeIf { it.isNotBlank() } ?: UncategorizedLabel,
        categoryId = categoryId?.takeIf { it.isNotBlank() },
        price = price.toMoney(),
        imageUrl = imageUrl,
        status = when {
            !available -> ItemStatus.SoldOut
            missingIngredients.isNotEmpty() -> ItemStatus.IngredientOut
            !ready -> ItemStatus.NoRecipe
            else -> ItemStatus.Ready
        },
        variants = variantGroups.map { group ->
            VariantGroup(group.id, group.name, group.required, group.choices.map { VariantOption(it.id, it.name) })
        },
        extras = extras.map { ExtraOption(it.id, it.name, it.price.toMoney()) },
    )
}

@Serializable
private class VariantGroupDto(
    val id: String,
    val name: String,
    val required: Boolean = false,
    val choices: List<VariantOptionDto> = emptyList(),
)

@Serializable
private class VariantOptionDto(val id: String, val name: String)

@Serializable
private class ExtraDto(val id: String, val name: String, val price: JsonElement)

@Serializable
private class PaymentMethodDto(
    val code: String,
    val label: String,
    @SerialName("needs_change") val needsChange: Boolean = false,
    val icon: String = "",
    val missing: List<String> = emptyList(),
    @SerialName("image_url") val imageUrl: String? = null,
    val note: String = "",
)

@Serializable
private class ReceiptNumberDto(@SerialName("receipt_number") val number: String)

@Serializable
private data class OrderRequestDto(
    @SerialName("order_type") val orderType: String,
    @SerialName("customer_name") val customerName: String?,
    @SerialName("table_no") val tableNo: String?,
    @SerialName("payment_method") val paymentMethod: String?,
    @SerialName("cash_received") val cashReceived: Long?,
    @SerialName("receipt_number") val receiptNumber: String?,
    @SerialName("client_id") val clientId: String,
    @SerialName("visitor_category_id") val visitorCategoryId: String? = null,
    @SerialName("visitor_gender_id") val visitorGenderId: String? = null,
    @SerialName("promo_id") val promoId: String? = null,
    @SerialName("customer_id") val customerId: String? = null,
    @SerialName("note_id") val noteId: String? = null,
    @SerialName("note_label") val noteLabel: String? = null,
    /** Bill yang dikerjakan dapur sekarang dan dibayar belakangan; metode dan promo dipilih saat membayar. */
    @SerialName("open_bill") val openBill: Boolean = false,
    val items: List<OrderItemRequestDto>,
    /** Hanya diisi untuk pesanan yang tertunda; pesanan langsung memakai jam server. */
    @SerialName("created_at") val createdAt: String? = null,
)

@Serializable
private class OrderItemRequestDto(
    @SerialName("menu_item_id") val menuItemId: String,
    @SerialName("qty") val quantity: Int,
    val note: String?,
    @SerialName("variant_ids") val variantIds: List<String>,
    val extras: List<ExtraRequestDto>,
)

@Serializable
private class ExtraRequestDto(
    @SerialName("extra_id") val id: String,
    @SerialName("qty") val quantity: Int,
)

@Serializable
private class OrderResponseDto(
    val total: JsonElement,
    @SerialName("cash_received") val cashReceived: JsonElement? = null,
    @SerialName("receipt_number") val receiptNumber: String? = null,
)

@Serializable
private class VisitorKindDto(val id: String, val name: String, @SerialName("asks_gender") val asksGender: Boolean = false)

@Serializable
private class VisitorGenderDto(val id: String, val name: String)

@Serializable
private class VisitorChoicesDto(val categories: List<VisitorKindDto> = emptyList(), val genders: List<VisitorGenderDto> = emptyList()) {
    fun toModel() = VisitorChoices(
        categories = categories.map { VisitorKind(it.id, it.name, it.asksGender) },
        genders = genders.map { VisitorGender(it.id, it.name) },
    )
}

@Serializable
private class CustomerSuggestionDto(
    val id: String,
    val name: String,
    val contact: String? = null,
    @SerialName("visit_count") val visitCount: Int = 0,
) {
    fun toModel() = CustomerSuggestion(id, name, contact, visitCount)
}

@Serializable
private class OrderNoteDto(val id: String, val name: String) {
    fun toModel() = OrderNote(id, name)
}

@Serializable
private class OrderNoteRequestDto(val name: String)

@Serializable
private class ActiveShiftDto(@SerialName("business_day") val businessDay: String)
