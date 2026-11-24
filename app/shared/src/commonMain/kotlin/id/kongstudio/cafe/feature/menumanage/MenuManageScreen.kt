package id.kongstudio.cafe.feature.menumanage

import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.resources.menu_form_invalid
import id.kongstudio.cafe.resources.sort_by_category
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_name
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.menu_available
import id.kongstudio.cafe.resources.menu_available_confirm
import id.kongstudio.cafe.resources.menu_available_message
import id.kongstudio.cafe.resources.menu_available_title
import id.kongstudio.cafe.resources.menu_fixed_cost
import id.kongstudio.cafe.resources.menu_marked_unavailable
import id.kongstudio.cafe.resources.menu_switched_off_all
import id.kongstudio.cafe.resources.menu_unavailable_confirm
import id.kongstudio.cafe.resources.menu_unavailable_message
import id.kongstudio.cafe.resources.menu_unavailable_title
import id.kongstudio.cafe.resources.menu_category
import id.kongstudio.cafe.resources.menu_delete_message
import id.kongstudio.cafe.resources.menu_delete_title
import id.kongstudio.cafe.resources.menu_description
import id.kongstudio.cafe.resources.menu_empty
import id.kongstudio.cafe.resources.menu_form_edit
import id.kongstudio.cafe.resources.menu_missing
import id.kongstudio.cafe.resources.menu_no_recipe
import id.kongstudio.cafe.resources.menu_search
import id.kongstudio.cafe.resources.nav_menu_manage
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.productcard.BlockedLabel
import id.kongstudio.cafe.ui.component.productcard.BlockedTone
import id.kongstudio.cafe.ui.component.photofield.PhotoField
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.remoteimage.RemoteThumbnail
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.defaultSortOption
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.resourcelist.timeSortOptions
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.feature.network.LiveChange
import kotlinx.coroutines.flow.Flow
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.ui.Alignment
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun MenuManageScreen(
    viewModel: PagedListViewModel<MenuEntry>,
    repository: MenuManageRepository,
    access: UserAccess,
    detailChanges: Flow<LiveChange>,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var categories by remember { mutableStateOf<List<MenuCategory>>(emptyList()) }
    var categoriesFailure by remember { mutableStateOf<AppFailure?>(null) }
    var editing by remember { mutableStateOf<MenuEntry?>(null) }
    var detailId by remember { mutableStateOf<String?>(null) }
    var deleting by remember { mutableStateOf<MenuEntry?>(null) }
    var toggling by remember { mutableStateOf<MenuEntry?>(null) }
    val canManage = access.allows(Permission.MenuManage)
    val canToggle = access.allows(Permission.MenuManage, Permission.MenuAvailability)
    val actionError = state.actionFailure?.let { failureText(it) }

    LaunchedEffect(repository) {
        when (val result = repository.categories()) {
            is DeviceResult.Ok -> {
                categories = result.value
                categoriesFailure = null
            }
            is DeviceResult.Failed -> categoriesFailure = result.failure
        }
    }
    val filters = listOf(ResourceFilter("", stringResource(Res.string.common_all))) +
        categories.map { ResourceFilter(it.id, it.name) }
    val title = stringResource(Res.string.nav_menu_manage)
    // Rincian dibaca dari daftar terbaru, supaya perubahan dari tablet atau web lain langsung terlihat di halaman yang terbuka.
    val detail = detailId?.let { id -> state.items.firstOrNull { it.id == id } }

    if (detail != null) {
        MenuDetailPage(
            entry = detail,
            blocked = blockedOf(detail),
            listTitle = title,
            repository = repository,
            changes = detailChanges,
            canManage = canManage,
            canToggle = canToggle,
            acting = state.acting,
            onBack = { detailId = null },
            onEdit = { editing = detail },
            onDelete = { deleting = detail },
            onToggle = { toggling = detail },
            modifier = modifier,
        )
    } else {
        ResourceList(
            title = title,
            items = state.items,
            page = state.page,
            pageCount = viewModel.pageCount,
            total = state.total,
            pageSize = viewModel.pageSize,
            onPageChange = viewModel::setPage,
            loading = state.loading,
            failure = state.failure,
            onRetry = viewModel::reload,
            emptyText = stringResource(Res.string.menu_empty),
            modifier = modifier,
            searchLabel = stringResource(Res.string.menu_search),
            query = state.query,
            onQueryChange = viewModel::setQuery,
            filters = filters,
            selectedFilter = state.filter,
            onFilterChange = viewModel::setFilter,
            sortLabel = sortLabel(),
            sortOptions = listOf(defaultSortOption(stringResource(Res.string.sort_by_category))) + nameSortOptions() + timeSortOptions(),
            selectedSort = state.sort,
            onSortChange = viewModel::setSort,
            actionError = actionError.takeIf { editing == null && deleting == null && toggling == null },
        ) { entry ->
            val blocked = blockedOf(entry)
            ListRow(
                title = entry.name,
                caption = entry.category,
                badge = when {
                    blocked != null -> { { BlockedLabel(text = blocked.first, tone = blocked.second) } }
                    entry.hasFixedCost -> { { StatusBadge(text = stringResource(Res.string.menu_fixed_cost), tone = BadgeTone.Neutral) } }
                    else -> null
                },
                // Foto menu menggantikan ikon begitu diunggah.
                leading = {
                    val photo = entry.imageUrl
                    if (photo != null) RemoteThumbnail(url = photo, contentDescription = entry.name) else IconBadge(AppIcons.Coffee)
                },
                // Harga ditonjolkan di kanan seperti stok di Daftar Bahan, saklar ketersediaan di sebelahnya.
                trailing = {
                    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md), verticalAlignment = Alignment.CenterVertically) {
                        AppText(text = formatRupiah(entry.price), role = TextRole.Title)
                        if (canToggle && !entry.switchedOffForAll) {
                            ToggleSwitch(
                                label = "",
                                accessibleName = stringResource(Res.string.menu_available),
                                checked = entry.available,
                                onCheckedChange = { toggling = entry },
                            )
                        }
                    }
                },
                opensDetail = true,
                onClick = { detailId = entry.id },
            )
        }
    }

    editing?.let { target ->
        MenuForm(
            entry = target,
            categories = categories,
            loadFailure = categoriesFailure,
            submitting = state.acting,
            error = actionError,
            onSubmit = { name, description, categoryId, available, image ->
                viewModel.act(onSuccess = { editing = null }) {
                    repository.update(target.id, name, description, categoryId, available, image)
                }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                editing = null
            },
        )
    }

    toggling?.let { entry ->
        val turnOff = entry.available
        ConfirmSheet(
            title = stringResource(if (turnOff) Res.string.menu_unavailable_title else Res.string.menu_available_title),
            message = stringResource(if (turnOff) Res.string.menu_unavailable_message else Res.string.menu_available_message, entry.name),
            confirmLabel = stringResource(if (turnOff) Res.string.menu_unavailable_confirm else Res.string.menu_available_confirm),
            destructive = turnOff,
            enabled = !state.acting,
            onConfirm = { viewModel.act(onSuccess = { toggling = null }) { repository.setAvailable(entry.id, !turnOff) } },
            onDismiss = {
                viewModel.clearActionFailure()
                toggling = null
            },
        )
    }

    deleting?.let { entry ->
        ConfirmSheet(
            title = stringResource(Res.string.menu_delete_title),
            message = stringResource(Res.string.menu_delete_message, entry.name),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            onConfirm = { viewModel.act(onSuccess = { deleting = null }) { repository.delete(entry.id) } },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
        )
    }
}

/** Satu penanda per menu menurut prioritas, berwarna sama dengan alasan yang sama di kartu Kasir; null bila menu bisa dijual. */
@Composable
private fun blockedOf(entry: MenuEntry): Pair<String, BlockedTone>? = when {
    entry.switchedOffForAll -> stringResource(Res.string.menu_switched_off_all) to BlockedTone.Danger
    !entry.available -> stringResource(Res.string.menu_marked_unavailable) to BlockedTone.Danger
    entry.hasFixedCost -> null
    entry.missingIngredients.isNotEmpty() ->
        stringResource(Res.string.menu_missing, entry.missingIngredients.joinToString(", ")) to BlockedTone.Warning
    !entry.readyToSell -> stringResource(Res.string.menu_no_recipe) to BlockedTone.Caution
    else -> null
}

@Composable
private fun MenuForm(
    entry: MenuEntry,
    categories: List<MenuCategory>,
    loadFailure: AppFailure?,
    submitting: Boolean,
    error: String?,
    onSubmit: (name: String, description: String, categoryId: String, available: Boolean, image: ByteArray?) -> Unit,
    onDismiss: () -> Unit,
) {
    var name by remember { mutableStateOf(entry.name) }
    var description by remember { mutableStateOf(entry.description.orEmpty()) }
    var categoryId by remember { mutableStateOf(entry.categoryId ?: categories.firstOrNull()?.id.orEmpty()) }
    var available by remember { mutableStateOf(entry.available) }
    var photo by remember { mutableStateOf<PickedPhoto?>(null) }

    FormSheet(
        title = stringResource(Res.string.menu_form_edit),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = { onSubmit(name, description, categoryId, available, photo?.bytes) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = name.isNotBlank() && categoryId.isNotBlank(),
        invalidMessage = stringResource(Res.string.menu_form_invalid),
        error = error ?: loadFailure?.let { failureText(it) },
    ) {
        AppTextField(value = name, onValueChange = { name = it }, label = stringResource(Res.string.common_name))
        ChoiceFlow(
            label = stringResource(Res.string.menu_category),
            options = categories.map { it.name },
            selectedIndex = categories.indexOfFirst { it.id == categoryId }.takeIf { it >= 0 },
            onSelect = { categoryId = categories[it].id },
        )
        AppTextField(
            value = description,
            onValueChange = { description = it },
            label = stringResource(Res.string.menu_description),
        )
        ToggleSwitch(
            label = stringResource(Res.string.menu_available),
            checked = available,
            onCheckedChange = { available = it },
        )
        PhotoField(photo = photo, onPicked = { photo = it }, enabled = !submitting)
    }
}
