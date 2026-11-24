package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.recipes.RecipeRepository
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_ingredient_list
import id.kongstudio.cafe.resources.stock_ingredients_empty
import id.kongstudio.cafe.resources.stock_search
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import org.jetbrains.compose.resources.stringResource

/** Daftar Bahan di tablet: stok tiap bahan sekarang; mengetuk bahan membuka detailnya. Harga dan data bahan diatur di web admin. */
@Composable
internal fun IngredientListScreen(
    viewModel: PagedListViewModel<StockIngredient>,
    recipes: RecipeRepository,
    /** Menu yang memakai satu bahan; dibuat pemanggil supaya umurnya ikut halaman detail. */
    uses: @Composable (ingredientId: String) -> PagedListViewModel<RecipeUse>,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var openedId by rememberSaveable { mutableStateOf<String?>(null) }
    var opened by remember { mutableStateOf<StockIngredient?>(null) }
    // Baris di halaman daftar ikut segar lewat live, jadi detail membaca dari sana; salinan saat diketuk hanya cadangan bila halaman berganti.
    val detail = openedId?.let { id -> state.items.firstOrNull { it.id == id } ?: opened?.takeIf { it.id == id } }

    if (detail != null) {
        IngredientDetailPage(
            ingredient = detail,
            uses = uses(detail.id),
            recipes = recipes,
            recipeAccess = RecipeAccess(
                canRead = access.allows(Permission.RecipeDetail, Permission.RecipeManage),
                canEdit = access.allows(Permission.RecipeManage),
            ),
            onBack = {
                openedId = null
                opened = null
            },
            modifier = modifier,
        )
        return
    }

    ResourceList(
        title = stringResource(Res.string.nav_ingredient_list),
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.stock_ingredients_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.stock_search),
        query = state.query,
        onQueryChange = viewModel::setQuery,
        sortLabel = sortLabel(),
        sortOptions = nameSortOptions(),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
    ) { ingredient ->
        IngredientRow(
            ingredient = ingredient,
            caption = ingredient.category,
            onClick = {
                opened = ingredient
                openedId = ingredient.id
            },
        )
    }
}
