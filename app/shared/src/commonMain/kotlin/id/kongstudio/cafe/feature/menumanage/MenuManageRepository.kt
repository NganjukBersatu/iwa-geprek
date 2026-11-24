package id.kongstudio.cafe.feature.menumanage

import id.kongstudio.cafe.core.format.rupiahOf
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.putText
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

internal const val MenuManagePageSize = 20

internal class MenuEntry(
    val id: String,
    val name: String,
    val description: String?,
    val price: Long,
    val categoryId: String?,
    val category: String?,
    val imageUrl: String?,
    val available: Boolean,
    /** Dimatikan admin untuk semua cabang; tablet tidak bisa menyalakannya. */
    val switchedOffForAll: Boolean,
    val readyToSell: Boolean,
    val missingIngredients: List<String>,
    /** Menu tanpa resep yang harga pokoknya diisi langsung; siap dijual tanpa resep. */
    val hasFixedCost: Boolean,
)

internal class MenuCategory(val id: String, val name: String)

internal class MenuVariantGroup(val name: String, val required: Boolean, val choices: List<String>)

internal class MenuExtra(val name: String, val price: Long)

/** Satu bahan resep: [qty] takaran satu porsi dan [stock] stok cabang, keduanya teks desimal dalam [unit]. */
internal class MenuRecipeLine(val ingredient: String, val unit: String?, val qty: String, val stock: String, val short: Boolean)

/** Bacaan halaman rincian menu; [recipe] null bila akun tidak berhak melihat resep. */
internal class MenuDetail(
    val entry: MenuEntry,
    val variantGroups: List<MenuVariantGroup>,
    val extras: List<MenuExtra>,
    val recipe: List<MenuRecipeLine>?,
    val portionsLeft: Int?,
    val makerStation: String?,
    val soldToday: Int,
    val costBasis: CostBasis,
)

/** Dasar harga pokok menu di cabang; nilai yang tidak dikenal dibaca [Unknown] supaya versi server baru tidak membuat tablet gagal. */
internal enum class CostBasis(val code: String) {
    Fixed("fixed"),
    Recipe("recipe"),
    Resale("resale"),
    None("none"),
    Unknown("");

    companion object {
        fun of(code: String) = entries.firstOrNull { it.code == code } ?: Unknown
    }
}

private const val MenuPath = "/v2/operational/menu"

/** Tabel di luar katalog yang mengubah isi halaman rincian menu: jumlah terjual dan stasiun pembuat. */
internal val MenuDetailOrderTables = setOf("orders", "order_items", "stations", "station_branch_settings", "category_stations", "category_branch_stations")

internal class MenuManageRepository(private val api: AdminApi) {
    suspend fun list(request: PageRequest): DeviceResult<ListPage<MenuEntry>> =
        when (
            val result = api.get(
                path = MenuPath,
                serializer = MenuPageDto.serializer(),
                query = mapOf(
                    "page" to request.page + 1,
                    "size" to MenuManagePageSize,
                    "category_id" to request.filter,
                    "search" to request.query,
                    "sort" to request.sort,
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    suspend fun detail(id: String): DeviceResult<MenuDetail> =
        when (val result = api.get(path = "$MenuPath/$id", serializer = MenuDetailDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    suspend fun categories(): DeviceResult<List<MenuCategory>> =
        when (
            val result = api.get(
                path = "$MenuPath/categories",
                serializer = ListSerializer(CategoryDto.serializer()),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.map { MenuCategory(it.id, it.name) })
        }

    suspend fun update(
        id: String,
        name: String,
        description: String,
        categoryId: String,
        available: Boolean,
        image: ByteArray?,
    ): DeviceResult<MenuEntry> {
        val updated = api.send(
            method = HttpMethod.Patch,
            path = "$MenuPath/$id",
            body = buildJsonObject {
                put("name", name.trim())
                putText("description", description)
                put("category_id", categoryId)
                put("is_available", available)
            },
            serializer = MenuDto.serializer(),
        )
        if (updated !is DeviceResult.Ok || image == null) return mapped(updated)
        val withImage = api.upload("$MenuPath/$id/photo", "file", image, MenuDto.serializer())
        return if (withImage is DeviceResult.Ok) mapped(withImage) else mapped(updated)
    }

    /** Staf yang bertugas boleh menandai menu habis lewat izin `menu.tersedia`, tanpa mengubah yang lain. */
    suspend fun setAvailable(id: String, available: Boolean): DeviceResult<MenuEntry> = mapped(
        api.send(
            method = HttpMethod.Patch,
            path = "$MenuPath/$id/availability",
            body = buildJsonObject { put("is_available", available) },
            serializer = MenuDto.serializer(),
        ),
    )

    suspend fun delete(id: String): DeviceResult<Unit> = api.sendUnit(HttpMethod.Delete, "$MenuPath/$id")

    private fun mapped(result: DeviceResult<MenuDto>): DeviceResult<MenuEntry> = when (result) {
        is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        is DeviceResult.Failed -> result
    }
}

@Serializable
private class MenuPageDto(val items: List<MenuDto>, val total: Int)

@Serializable
private class CategoryDto(val id: String, val name: String)

@Serializable
private class VariantGroupDto(val name: String, val required: Boolean = false, val choices: List<String> = emptyList())

@Serializable
private class ExtraDto(val name: String, val price: String = "0")

@Serializable
private class RecipeLineDto(
    @SerialName("ingredient_name") val ingredient: String,
    val unit: String? = null,
    val qty: String,
    val stock: String,
    val short: Boolean = false,
)

@Serializable
private class MenuDetailDto(
    val menu: MenuDto,
    @SerialName("variant_groups") val variantGroups: List<VariantGroupDto> = emptyList(),
    val extras: List<ExtraDto> = emptyList(),
    val recipe: List<RecipeLineDto>? = null,
    @SerialName("portions_left") val portionsLeft: Int? = null,
    @SerialName("maker_station") val makerStation: String? = null,
    @SerialName("sold_today") val soldToday: Int = 0,
    @SerialName("cost_basis") val costBasis: String = "",
) {
    fun toModel() = MenuDetail(
        entry = menu.toModel(),
        variantGroups = variantGroups.map { MenuVariantGroup(it.name, it.required, it.choices) },
        extras = extras.map { MenuExtra(it.name, rupiahOf(it.price)) },
        recipe = recipe?.map { MenuRecipeLine(it.ingredient, it.unit, it.qty, it.stock, it.short) },
        portionsLeft = portionsLeft,
        makerStation = makerStation,
        soldToday = soldToday,
        costBasis = CostBasis.of(costBasis),
    )
}

@Serializable
private class MenuDto(
    val id: String,
    val name: String,
    val description: String? = null,
    val price: String = "0",
    @SerialName("category_id") val categoryId: String? = null,
    @SerialName("category_name") val category: String? = null,
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("is_available") val available: Boolean = true,
    @SerialName("switched_off_for_all") val switchedOffForAll: Boolean = false,
    @SerialName("ready_to_sell") val readyToSell: Boolean = true,
    @SerialName("missing_ingredients") val missingIngredients: List<String> = emptyList(),
    @SerialName("has_fixed_cost") val hasFixedCost: Boolean = false,
) {
    fun toModel() = MenuEntry(
        id = id,
        name = name,
        description = description?.takeIf { it.isNotBlank() },
        price = rupiahOf(price),
        categoryId = categoryId,
        category = category,
        imageUrl = imageUrl,
        available = available,
        switchedOffForAll = switchedOffForAll,
        readyToSell = readyToSell,
        missingIngredients = missingIngredients,
        hasFixedCost = hasFixedCost,
    )
}
