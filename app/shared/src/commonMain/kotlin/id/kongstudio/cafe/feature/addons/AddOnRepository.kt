package id.kongstudio.cafe.feature.addons

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val AddOnTables = setOf("variant_groups", "variant_choices", "menu_variant_groups", "extras", "extra_outlet_prices", "menu_extras", "menu_items")

/** Daftar tidak berhalaman, jadi satu halaman besar memuat semuanya. */
internal const val AddOnPageSize = 100
internal const val KindVariant = "varian"
internal const val KindExtra = "ekstra"
private const val OptionsPath = "/v2/operational/options"

/** [color] diatur di web dan hanya dibawa kembali saat menyimpan supaya tidak terhapus. */
internal class VariantChoice(val id: String?, val name: String, val active: Boolean, val color: String? = null)

/** Satu kelompok varian atau satu ekstra; [choices] dan [required] hanya bermakna untuk varian, [price] untuk ekstra. */
internal class AddOn(
    val id: String,
    val kind: String,
    val name: String,
    val active: Boolean,
    val required: Boolean,
    val choices: List<VariantChoice>,
    val price: Long,
    val menuIds: List<String>,
    /** Milik cabang tablet ini saja, jadi boleh diubah dari sini; yang berlaku di banyak cabang diubah dari web admin. */
    val editable: Boolean,
)

internal class MenuOption(val id: String, val name: String)

internal class AddOnRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest): DeviceResult<ListPage<AddOn>> {
        val kind = request.filter.ifEmpty { KindVariant }
        return if (kind == KindVariant) {
            when (val result = api.get("$OptionsPath/variant-groups", ListSerializer(VariantDto.serializer()))) {
                is DeviceResult.Failed -> result
                is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() }.let { ListPage(it, it.size) })
            }
        } else {
            when (val result = api.get("$OptionsPath/extras", ListSerializer(ExtraDto.serializer()))) {
                is DeviceResult.Failed -> result
                is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { it.toModel() }.let { ListPage(it, it.size) })
            }
        }
    }

    suspend fun menus(): DeviceResult<List<MenuOption>> =
        when (val result = api.get("$OptionsPath/menus", ListSerializer(MenuNameDto.serializer()))) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { MenuOption(it.id, it.name) })
        }

    suspend fun saveVariant(
        existing: AddOn?,
        name: String,
        required: Boolean,
        active: Boolean,
        choices: List<VariantChoice>,
        menuIds: List<String>,
    ): DeviceResult<Unit> = api.sendUnit(
        method = if (existing == null) HttpMethod.Post else HttpMethod.Put,
        path = if (existing == null) "$OptionsPath/variant-groups" else "$OptionsPath/variant-groups/${existing.id}",
        body = buildJsonObject {
            put("name", name.trim())
            put("required", required)
            put("is_active", active)
            put(
                "choices",
                buildJsonArray {
                    choices.forEach { choice ->
                        add(
                            buildJsonObject {
                                choice.id?.let { put("id", it) }
                                put("name", choice.name.trim())
                                choice.color?.let { put("color", it) }
                                put("is_active", choice.active)
                            },
                        )
                    }
                },
            )
            put("menu_ids", stringArray(menuIds))
        },
    )

    suspend fun saveExtra(
        existing: AddOn?,
        name: String,
        price: Long,
        active: Boolean,
        menuIds: List<String>,
    ): DeviceResult<Unit> = api.sendUnit(
        method = if (existing == null) HttpMethod.Post else HttpMethod.Put,
        path = if (existing == null) "$OptionsPath/extras" else "$OptionsPath/extras/${existing.id}",
        body = buildJsonObject {
            put("name", name.trim())
            put("price", price)
            put("is_active", active)
            put("menu_ids", stringArray(menuIds))
        },
    )

    suspend fun delete(item: AddOn): DeviceResult<Unit> = api.sendUnit(
        HttpMethod.Delete,
        if (item.kind == KindVariant) "$OptionsPath/variant-groups/${item.id}" else "$OptionsPath/extras/${item.id}",
    )

    private fun stringArray(values: List<String>): JsonArray = buildJsonArray { values.forEach { add(JsonPrimitive(it)) } }
}

@Serializable
private class MenuNameDto(val id: String, val name: String)

@Serializable
private class ChoiceDto(
    val id: String,
    val name: String,
    val color: String? = null,
    @SerialName("is_active") val active: Boolean = true,
)

@Serializable
private class VariantDto(
    val id: String,
    val name: String,
    val required: Boolean = true,
    @SerialName("is_active") val active: Boolean = true,
    val choices: List<ChoiceDto> = emptyList(),
    @SerialName("menu_ids") val menuIds: List<String> = emptyList(),
    val editable: Boolean = false,
) {
    fun toModel() = AddOn(
        id = id,
        kind = KindVariant,
        name = name,
        active = active,
        required = required,
        choices = choices.map { VariantChoice(it.id, it.name, it.active, it.color) },
        price = 0,
        menuIds = menuIds,
        editable = editable,
    )
}

@Serializable
private class ExtraDto(
    val id: String,
    val name: String,
    val price: JsonElement? = null,
    @SerialName("is_active") val active: Boolean = true,
    @SerialName("menu_ids") val menuIds: List<String> = emptyList(),
    val editable: Boolean = false,
) {
    fun toModel() = AddOn(
        id = id,
        kind = KindExtra,
        name = name,
        active = active,
        required = false,
        choices = emptyList(),
        price = price.toMoney(),
        menuIds = menuIds,
        editable = editable,
    )
}
