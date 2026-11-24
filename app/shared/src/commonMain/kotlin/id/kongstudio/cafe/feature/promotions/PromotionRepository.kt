package id.kongstudio.cafe.feature.promotions

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val PromotionTables = setOf("promos", "cafe_promotions", "menu_items")

/** Daftar tidak berhalaman, jadi satu halaman besar memuat semuanya. */
internal const val PromotionPageSize = 100
internal const val KindDiscount = "diskon"
internal const val KindInfo = "info"
private const val PromotionsPath = "/v2/operational/promotions"

internal enum class DiscountScope(val code: String) { Basic("basic"), Product("produk"), Total("total") }

internal enum class DiscountType(val code: String) { Percent("persen"), Amount("nominal") }

internal enum class Activation(val code: String) { Auto("otomatis"), Manual("manual") }

internal class Promotion(
    val id: String,
    val kind: String,
    val title: String,
    val description: String,
    val scope: DiscountScope,
    val type: DiscountType,
    val value: Long,
    val productIds: List<String>,
    val minSpend: Long?,
    val activation: Activation,
    val imageUrl: String?,
    val from: String,
    val to: String,
    val active: Boolean,
    /** Milik cabang tablet ini saja, jadi boleh diubah dari sini; yang berlaku di semua cabang diubah dari web admin. */
    val editable: Boolean,
)

internal class PromotionMenu(val id: String, val name: String)

/** Isian formulir; satu bentuk untuk diskon kasir dan info kafe, bidang yang tidak relevan diabaikan. */
internal class PromotionForm(
    val title: String,
    val description: String,
    val scope: DiscountScope,
    val type: DiscountType,
    val value: Long,
    val productIds: List<String>,
    val minSpend: Long?,
    val activation: Activation,
    val imageUrl: String,
    val from: String,
    val to: String,
    val active: Boolean,
)

internal class PromotionRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest): DeviceResult<ListPage<Promotion>> {
        val kind = request.filter.ifEmpty { KindDiscount }
        return if (kind == KindDiscount) {
            when (val result = api.get("$PromotionsPath/discounts", ListSerializer(DiscountDto.serializer()))) {
                is DeviceResult.Failed -> result
                is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() }.let { ListPage(it, it.size) })
            }
        } else {
            when (val result = api.get("$PromotionsPath/announcements", ListSerializer(InfoDto.serializer()))) {
                is DeviceResult.Failed -> result
                is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() }.let { ListPage(it, it.size) })
            }
        }
    }

    suspend fun menus(): DeviceResult<List<PromotionMenu>> =
        when (val result = api.get("$PromotionsPath/menus", ListSerializer(MenuNameDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { PromotionMenu(it.id, it.name) })
        }

    suspend fun save(existing: Promotion?, kind: String, form: PromotionForm): DeviceResult<Unit> {
        val base = basePath(kind)
        return api.sendUnit(
            method = if (existing == null) HttpMethod.Post else HttpMethod.Patch,
            path = if (existing == null) base else "$base/${existing.id}",
            body = if (kind == KindDiscount) discountBody(form) else infoBody(form, existing),
        )
    }

    suspend fun toggle(item: Promotion): DeviceResult<Unit> =
        api.sendUnit(HttpMethod.Patch, "${basePath(item.kind)}/${item.id}", buildJsonObject { put("is_active", !item.active) })

    suspend fun delete(item: Promotion): DeviceResult<Unit> = api.sendUnit(HttpMethod.Delete, "${basePath(item.kind)}/${item.id}")

    private fun basePath(kind: String) = if (kind == KindDiscount) "$PromotionsPath/discounts" else "$PromotionsPath/announcements"

    private fun discountBody(form: PromotionForm) = buildJsonObject {
        put("name", form.title.trim())
        putText("description", form.description)
        put("kind", form.scope.code)
        put("discount_type", form.type.code)
        put("value", form.value)
        if (form.scope == DiscountScope.Product) {
            put("product_ids", buildJsonArray { form.productIds.forEach { add(JsonPrimitive(it)) } })
        } else {
            put("product_ids", JsonNull)
        }
        val minSpend = form.minSpend.takeIf { form.scope == DiscountScope.Total }
        if (minSpend != null) put("minimum_spend", minSpend) else put("minimum_spend", JsonNull)
        put("activation", form.activation.code)
        put("starts_on", form.from)
        put("ends_on", form.to)
        put("is_active", form.active)
    }

    /** Gambar hanya dikirim bila diubah, supaya gambar unggahan dari web tidak berubah menjadi tautan. */
    private fun infoBody(form: PromotionForm, existing: Promotion?) = buildJsonObject {
        put("title", form.title.trim())
        put("description", form.description.trim())
        if (existing == null || form.imageUrl.trim() != existing.imageUrl.orEmpty()) putText("image_link", form.imageUrl)
        put("starts_on", form.from)
        put("ends_on", form.to)
        put("is_active", form.active)
    }
}

@Serializable
private class MenuNameDto(val id: String, val name: String)

@Serializable
private class DiscountDto(
    val id: String,
    @SerialName("name") val title: String,
    val description: String? = null,
    @SerialName("kind") val scope: String = "basic",
    @SerialName("discount_type") val type: String = "persen",
    val value: JsonElement? = null,
    @SerialName("product_ids") val productIds: List<String>? = null,
    @SerialName("minimum_spend") val minSpend: JsonElement? = null,
    val activation: String = "otomatis",
    @SerialName("starts_on") val from: String,
    @SerialName("ends_on") val to: String,
    @SerialName("is_active") val active: Boolean = true,
    val editable: Boolean = false,
) {
    fun toModel() = Promotion(
        id = id,
        kind = KindDiscount,
        title = title,
        description = description.orEmpty(),
        scope = DiscountScope.entries.firstOrNull { it.code == scope } ?: DiscountScope.Basic,
        type = DiscountType.entries.firstOrNull { it.code == type } ?: DiscountType.Percent,
        value = value.toMoney(),
        productIds = productIds.orEmpty(),
        minSpend = minSpend.toMoneyOrNull(),
        activation = Activation.entries.firstOrNull { it.code == activation } ?: Activation.Auto,
        imageUrl = null,
        from = from,
        to = to,
        active = active,
        editable = editable,
    )
}

@Serializable
private class InfoDto(
    val id: String,
    val title: String,
    val description: String = "",
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("starts_on") val from: String,
    @SerialName("ends_on") val to: String,
    @SerialName("is_active") val active: Boolean = true,
    val editable: Boolean = false,
) {
    fun toModel() = Promotion(
        id = id,
        kind = KindInfo,
        title = title,
        description = description,
        scope = DiscountScope.Basic,
        type = DiscountType.Percent,
        value = 0,
        productIds = emptyList(),
        minSpend = null,
        activation = Activation.Auto,
        imageUrl = imageUrl?.takeIf { it.isNotBlank() },
        from = from,
        to = to,
        active = active,
        editable = editable,
    )
}
