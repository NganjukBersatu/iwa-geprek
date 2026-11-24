package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.recipes.RecipeEntry
import id.kongstudio.cafe.feature.recipes.RecipeRepository
import id.kongstudio.cafe.feature.recipes.RecipeSheet
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_ingredients
import id.kongstudio.cafe.resources.ingredient_category
import id.kongstudio.cafe.resources.ingredient_minimum
import id.kongstudio.cafe.resources.ingredient_status
import id.kongstudio.cafe.resources.ingredient_stock_now
import id.kongstudio.cafe.resources.ingredient_unit
import id.kongstudio.cafe.resources.ingredient_use_qty
import id.kongstudio.cafe.resources.ingredient_used_empty
import id.kongstudio.cafe.resources.ingredient_used_in
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.subpage.SubPage
import org.jetbrains.compose.resources.stringResource

/** Lembar Resep hanya dibuka bagi yang boleh membaca resep; menyimpan tetap butuh izin kelola resep, dan server memeriksa keduanya. */
internal class RecipeAccess(val canRead: Boolean, val canEdit: Boolean)

/** Detail satu bahan dari Daftar Bahan: info bahan dan menu yang memakainya; riwayat dan stok awal ada di Stok Opname. */
@Composable
internal fun IngredientDetailPage(
    ingredient: StockIngredient,
    uses: PagedListViewModel<RecipeUse>,
    recipes: RecipeRepository,
    recipeAccess: RecipeAccess,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by uses.state.collectAsState()
    var recipe by remember { mutableStateOf<RecipeEntry?>(null) }

    SubPage(
        title = ingredient.name,
        backLabel = stringResource(Res.string.back_to_ingredients),
        onBack = onBack,
        modifier = modifier,
        canLeave = !state.acting,
    ) {
        DetailCard(
            rows = listOf(
                stringResource(Res.string.ingredient_unit) to ingredient.unit,
                stringResource(Res.string.ingredient_category) to ingredient.category,
                stringResource(Res.string.ingredient_stock_now) to StockQuantity.withUnit(ingredient.stock, ingredient.unit),
                stringResource(Res.string.ingredient_minimum) to StockQuantity.withUnit(ingredient.minimum, ingredient.unit),
                stringResource(Res.string.ingredient_status) to stringResource(stockStatusLabel(ingredient)),
            ),
        )

        SectionTitle(text = stringResource(Res.string.ingredient_used_in), padded = false)
        state.failure?.let { InlineMessage(text = failureText(it)) }
        if (recipe == null) state.actionFailure?.let { InlineMessage(text = failureText(it)) }
        PagedListCard(
            items = state.items,
            page = state.page,
            pageCount = uses.pageCount,
            onPageChange = uses::setPage,
            emptyText = stringResource(Res.string.ingredient_used_empty),
            loading = state.loading,
        ) { use ->
            ListRow(
                title = use.menuName,
                detail = stringResource(Res.string.ingredient_use_qty, StockQuantity.withUnit(use.qty, ingredient.unit)),
                opensDetail = true,
                onClick = if (recipeAccess.canRead) {
                    {
                        uses.clearActionFailure()
                        uses.act {
                            recipes.one(use.menuId).also { result -> if (result is DeviceResult.Ok) recipe = result.value }
                        }
                    }
                } else {
                    null
                },
            )
        }
    }

    recipe?.let { entry ->
        RecipeSheet(
            entry = entry,
            repository = recipes,
            canEdit = recipeAccess.canEdit,
            submitting = state.acting,
            error = state.actionFailure?.let { failureText(it) },
            onSave = { lines -> uses.act(onSuccess = { recipe = null }) { recipes.save(entry.menuId, lines) } },
            onDismiss = {
                uses.clearActionFailure()
                recipe = null
            },
        )
    }
}
