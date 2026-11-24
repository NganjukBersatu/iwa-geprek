package id.kongstudio.cafe.feature.recipes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.isQuantityTyping
import id.kongstudio.cafe.core.format.quantityOf
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.admin.rememberChoicePages
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.nav_recipes
import id.kongstudio.cafe.resources.recipe_add_ingredient
import id.kongstudio.cafe.resources.recipe_cost
import id.kongstudio.cafe.resources.recipe_empty
import id.kongstudio.cafe.resources.recipe_filter_with
import id.kongstudio.cafe.resources.recipe_filter_without
import id.kongstudio.cafe.resources.recipe_form_invalid
import id.kongstudio.cafe.resources.recipe_line_removed
import id.kongstudio.cafe.resources.recipe_line_undo
import id.kongstudio.cafe.resources.recipe_lines
import id.kongstudio.cafe.resources.recipe_margin
import id.kongstudio.cafe.resources.recipe_no_lines
import id.kongstudio.cafe.resources.recipe_read_only
import id.kongstudio.cafe.resources.recipe_remove
import id.kongstudio.cafe.resources.recipe_search
import id.kongstudio.cafe.resources.recipe_search_ingredient
import id.kongstudio.cafe.resources.recipe_sheet_title
import id.kongstudio.cafe.resources.recipe_state_none
import id.kongstudio.cafe.resources.sort_by_category
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.defaultSortOption
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import id.kongstudio.cafe.resources.recipe_quantity_per_portion
import org.jetbrains.compose.resources.stringResource

private const val SuggestionLimit = 8
private const val SuggestionSkeletonRows = 2

@Composable
internal fun RecipeScreen(
    viewModel: PagedListViewModel<RecipeEntry>,
    repository: RecipeRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var editing by remember { mutableStateOf<RecipeEntry?>(null) }
    val canEdit = access.allows(Permission.RecipeManage)
    val canSeeCost = access.allows(Permission.RecipeDetail)
    val filters = listOf(
        ResourceFilter("", stringResource(Res.string.common_all)),
        ResourceFilter(FilterWithRecipe, stringResource(Res.string.recipe_filter_with)),
        ResourceFilter(FilterWithoutRecipe, stringResource(Res.string.recipe_filter_without)),
    )

    ResourceList(
        title = stringResource(Res.string.nav_recipes),
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.recipe_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.recipe_search),
        query = state.query,
        onQueryChange = viewModel::setQuery,
        filters = filters,
        selectedFilter = state.filter,
        onFilterChange = viewModel::setFilter,
        sortLabel = sortLabel(),
        sortOptions = listOf(defaultSortOption(stringResource(Res.string.sort_by_category))) + nameSortOptions(),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
        actionError = state.actionFailure?.let { failureText(it) }.takeIf { editing == null },
    ) { entry ->
        ListRow(
            title = entry.menuName,
            detail = if (entry.hasRecipe) {
                stringResource(Res.string.recipe_lines, entry.lines.size)
            } else {
                stringResource(Res.string.recipe_state_none)
            },
            caption = entry.category,
            leading = { IconBadge(AppIcons.KitchenTools) },
            // HPP ditonjolkan di kanan seperti harga di Kelola Menu, margin di bawahnya; hanya untuk yang berhak melihat biaya.
            trailing = if (canSeeCost && entry.cost != null) {
                {
                    Column(horizontalAlignment = Alignment.End) {
                        AppText(text = stringResource(Res.string.recipe_cost, formatRupiah(entry.cost)), role = TextRole.Title)
                        entry.marginPercent?.let {
                            AppText(text = stringResource(Res.string.recipe_margin, it), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                        }
                    }
                }
            } else {
                null
            },
            opensDetail = true,
            onClick = { editing = entry },
        )
    }

    editing?.let { entry ->
        RecipeSheet(
            entry = entry,
            repository = repository,
            canEdit = canEdit,
            submitting = state.acting,
            error = state.actionFailure?.let { failureText(it) },
            onSave = { lines ->
                viewModel.act(onSuccess = { editing = null }) { repository.save(entry.menuId, lines) }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                editing = null
            },
        )
    }
}

/** Lembar Resep satu menu; dipakai Master Resep dan daftar "Dipakai di menu" di detail bahan. */
@Composable
internal fun RecipeSheet(
    entry: RecipeEntry,
    repository: RecipeRepository,
    canEdit: Boolean,
    submitting: Boolean,
    error: String?,
    onSave: (List<RecipeLine>) -> Unit,
    onDismiss: () -> Unit,
) {
    val lines = remember(entry.menuId) { mutableStateListOf<RecipeLine>().apply { addAll(entry.lines) } }
    // Saran dicari di server hanya saat ada kata cari; kosong berarti tidak ada saran.
    val ingredients = rememberChoicePages<Ingredient>(key = { it.id }) { query, page ->
        if (query.isEmpty()) DeviceResult.Ok(ChoicePage(emptyList(), hasMore = false)) else repository.ingredients(query, page, SuggestionLimit)
    }
    var removedLine by remember { mutableStateOf<Pair<Int, RecipeLine>?>(null) }
    var search by remember { mutableStateOf("") }
    val suggestions = ingredients.items.filter { candidate -> search.isNotBlank() && lines.none { it.ingredientId == candidate.id } }

    val quantitiesValid = lines.all { line -> quantityOf(line.quantity) != null }

    FormSheet(
        title = stringResource(Res.string.recipe_sheet_title, entry.menuName),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = { onSave(lines.toList()) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = canEdit && quantitiesValid,
        invalidMessage = stringResource(if (canEdit) Res.string.recipe_form_invalid else Res.string.recipe_read_only),
        error = error ?: ingredients.failure?.let { failureText(it) },
    ) {
        SectionTitle(text = stringResource(Res.string.recipe_lines, lines.size), padded = false)
        if (lines.isEmpty()) Notice(stringResource(Res.string.recipe_no_lines))
        lines.forEachIndexed { index, line ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    AppText(
                        text = line.name,
                        role = TextRole.Body,
                        color = AppTheme.colors.content,
                    )
                    QuantityField(
                        value = line.quantity,
                        onValueChange = { if (isQuantityTyping(it)) lines[index] = RecipeLine(line.ingredientId, line.name, line.unit, it) },
                        label = stringResource(Res.string.recipe_quantity_per_portion),
                        unit = line.unit,
                        enabled = canEdit,
                        isError = line.quantity.isNotEmpty() && quantityOf(line.quantity) == null,
                    )
                }
                if (canEdit) {
                    AppIconButton(
                        icon = AppIcons.Close,
                        contentDescription = stringResource(Res.string.recipe_remove),
                        onClick = { removedLine = index to lines.removeAt(index) },
                    )
                }
            }
        }
        removedLine?.let { (position, line) ->
            StatusBanner(
                text = stringResource(Res.string.recipe_line_removed),
                tone = BannerTone.Info,
                actionLabel = stringResource(Res.string.recipe_line_undo),
                onAction = {
                    lines.add(position.coerceAtMost(lines.size), line)
                    removedLine = null
                },
            )
        }
        if (canEdit) {
            AppTextField(
                value = search,
                onValueChange = {
                    search = it
                    ingredients.search(it)
                },
                label = stringResource(Res.string.recipe_search_ingredient),
            )
            if (search.isNotBlank() && ingredients.searching) {
                SkeletonRows(count = SuggestionSkeletonRows)
            } else if (suggestions.isNotEmpty()) {
                ChoiceFlow(
                    label = stringResource(Res.string.recipe_add_ingredient),
                    options = suggestions.map { "${it.name} (${it.unit})" },
                    selectedIndex = null,
                    onSelect = { index ->
                        val picked = suggestions[index]
                        lines.add(RecipeLine(picked.id, picked.name, picked.unit, ""))
                        search = ""
                        ingredients.search("")
                    },
                )
            }
        }
    }
}
