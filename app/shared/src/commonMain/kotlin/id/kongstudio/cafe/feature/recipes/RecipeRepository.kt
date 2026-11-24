package id.kongstudio.cafe.feature.recipes

import id.kongstudio.cafe.core.format.quantityOf
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.admin.ListPage
import id.kongstudio.cafe.feature.admin.PageRequest
import id.kongstudio.cafe.feature.admin.toMoney
import id.kongstudio.cafe.feature.admin.toMoneyOrNull
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import io.ktor.http.HttpMethod
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Tabel yang perubahannya membuat layar ini memuat ulang; namanya sama dengan nama tabel di backend.
internal val RecipeTables = setOf("recipe_ingredients", "ingredients", "menu_items", "recipe_add_costs")

internal const val RecipePageSize = 20
internal const val FilterWithRecipe = "ada"
internal const val FilterWithoutRecipe = "belum"

internal class RecipeLine(val ingredientId: String, val name: String, val unit: String, val quantity: String)

internal class RecipeEntry(
    val menuId: String,
    val menuName: String,
    val category: String?,
    val price: Long,
    val hasRecipe: Boolean,
    val cost: Long?,
    val marginPercent: Long?,
    val lines: List<RecipeLine>,
)

internal class Ingredient(val id: String, val name: String, val unit: String)

private const val RecipesPath = "/v2/operational/recipes"

/** Resep per menu di cabang tablet; pencarian, penyaring, dan halaman dikerjakan server. */
internal class RecipeRepository(private val api: AdminApi) {

    suspend fun list(request: PageRequest): DeviceResult<ListPage<RecipeEntry>> =
        when (
            val result = api.get(
                path = RecipesPath,
                serializer = RecipePageDto.serializer(),
                query = mapOf(
                    "sort" to request.sort,
                    "page" to request.page + 1,
                    "size" to RecipePageSize,
                    "search" to request.query,
                    "recipe" to request.filter,
                ),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ListPage(result.value.items.map { it.toModel() }, result.value.total))
        }

    /** Satu resep menu di cabang tablet, untuk lembar Resep yang dibuka dari luar Master Resep. */
    suspend fun one(menuId: String): DeviceResult<RecipeEntry> =
        when (val result = api.get(path = "$RecipesPath/$menuId", serializer = RecipeDto.serializer())) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(result.value.toModel())
        }

    /** Dicari dan dimuat per halaman di server, supaya cabang dengan ribuan bahan tidak memuat semuanya; [page] berbasis nol. */
    suspend fun ingredients(search: String, page: Int, size: Int): DeviceResult<ChoicePage<Ingredient>> =
        when (
            val result = api.get(
                "$RecipesPath/ingredients",
                ListSerializer(IngredientDto.serializer()),
                mapOf("search" to search, "page" to page + 1, "size" to size),
            )
        ) {
            is DeviceResult.Failed -> result
            is DeviceResult.Ok -> DeviceResult.Ok(ChoicePage(result.value.map { Ingredient(it.id, it.name, it.unit.orEmpty()) }, hasMore = result.value.size == size))
        }

    /** Mengganti seluruh resep menu; daftar kosong menghapus resepnya. */
    suspend fun save(menuId: String, lines: List<RecipeLine>): DeviceResult<Unit> =
        api.sendUnit(
            method = HttpMethod.Put,
            path = "$RecipesPath/$menuId",
            body = buildJsonObject {
                put(
                    "lines",
                    buildJsonArray {
                        lines.forEach { line ->
                            add(
                                buildJsonObject {
                                    put("ingredient_id", line.ingredientId)
                                    put("qty", quantityOf(line.quantity))
                                },
                            )
                        }
                    },
                )
            },
        )
}

@Serializable
private class IngredientDto(val id: String, val name: String, val unit: String? = null)

@Serializable
private class LineDto(
    @SerialName("ingredient_id") val ingredientId: String,
    @SerialName("ingredient_name") val name: String,
    val unit: String? = null,
    @SerialName("qty") val quantity: JsonElement? = null,
)

@Serializable
private class RecipePageDto(val items: List<RecipeDto>, val total: Int)

@Serializable
private class RecipeDto(
    @SerialName("menu_id") val menuId: String,
    @SerialName("menu_name") val menuName: String,
    @SerialName("category_name") val category: String? = null,
    val price: JsonElement? = null,
    @SerialName("has_recipe") val hasRecipe: Boolean = false,
    @SerialName("final_cost") val cost: JsonElement? = null,
    @SerialName("margin_percent") val marginPercent: JsonElement? = null,
    val lines: List<LineDto> = emptyList(),
) {
    fun toModel() = RecipeEntry(
        menuId = menuId,
        menuName = menuName,
        category = category,
        price = price.toMoney(),
        hasRecipe = hasRecipe,
        cost = cost.toMoneyOrNull(),
        marginPercent = marginPercent.toMoneyOrNull(),
        lines = lines.map {
            RecipeLine(it.ingredientId, it.name, it.unit.orEmpty(), (it.quantity as? JsonPrimitive)?.content.orEmpty())
        },
    )
}
