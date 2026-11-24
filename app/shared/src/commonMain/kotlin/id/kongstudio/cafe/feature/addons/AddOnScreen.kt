package id.kongstudio.cafe.feature.addons

import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
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
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.resources.addon_extra_invalid
import id.kongstudio.cafe.resources.addon_variant_invalid
import id.kongstudio.cafe.resources.addon_add_extra
import id.kongstudio.cafe.resources.addon_add_variant
import id.kongstudio.cafe.resources.addon_choice_add
import id.kongstudio.cafe.resources.addon_choice_remove
import id.kongstudio.cafe.resources.addon_choices
import id.kongstudio.cafe.resources.addon_delete_message
import id.kongstudio.cafe.resources.addon_delete_title
import id.kongstudio.cafe.resources.addon_empty
import id.kongstudio.cafe.resources.addon_extra
import id.kongstudio.cafe.resources.addon_form_add
import id.kongstudio.cafe.resources.addon_form_edit
import id.kongstudio.cafe.resources.addon_menus
import id.kongstudio.cafe.resources.addon_price
import id.kongstudio.cafe.resources.addon_required
import id.kongstudio.cafe.resources.addon_variant
import id.kongstudio.cafe.resources.common_active
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_inactive
import id.kongstudio.cafe.resources.common_name
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.nav_variants_extras
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.multichoiceflow.MultiChoiceFlow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.textlisteditor.TextListEditor
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.ScopedActiveBadge
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun AddOnScreen(
    viewModel: PagedListViewModel<AddOn>,
    repository: AddOnRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var menus by remember { mutableStateOf<List<MenuOption>>(emptyList()) }
    var menusFailure by remember { mutableStateOf<AppFailure?>(null) }
    var creating by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<AddOn?>(null) }
    var deleting by remember { mutableStateOf<AddOn?>(null) }
    val kind = state.filter.ifEmpty { KindVariant }
    val canManage = if (kind == KindVariant) access.allows(Permission.VariantManage) else access.allows(Permission.ExtraManage)
    val actionError = state.actionFailure?.let { failureText(it) }

    LaunchedEffect(repository) {
        when (val result = repository.menus()) {
            is DeviceResult.Ok -> {
                menus = result.value
                menusFailure = null
            }
            is DeviceResult.Failed -> menusFailure = result.failure
        }
    }
    val filters = listOf(
        ResourceFilter(KindVariant, stringResource(Res.string.addon_variant)),
        ResourceFilter(KindExtra, stringResource(Res.string.addon_extra)),
    )

    ResourceList(
        title = stringResource(Res.string.nav_variants_extras),
        items = state.items,
        page = 0,
        pageCount = 1,
        total = state.items.size,
        pageSize = state.items.size.coerceAtLeast(1),
        onPageChange = {},
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.addon_empty),
        modifier = modifier,
        tabs = filters,
        selectedTab = kind,
        onTabChange = viewModel::setFilter,
        addLabel = stringResource(if (kind == KindVariant) Res.string.addon_add_variant else Res.string.addon_add_extra).takeIf { canManage },
        onAdd = { creating = true }.takeIf { canManage },
        actionError = actionError.takeIf { !creating && editing == null && deleting == null },
    ) { item ->
        ListRow(
            title = item.name,
            detail = if (item.kind == KindVariant) item.choices.joinToString(", ") { it.name } else null,
            caption = if (item.kind == KindVariant && item.required) stringResource(Res.string.addon_required) else null,
            badge = { ScopedActiveBadge(item.active, allBranches = !item.editable) },
            leading = { IconBadge(AppIcons.Adjustments) },
            trailing = if (item.kind == KindExtra) {
                { AppText(text = formatRupiah(item.price), role = TextRole.Title) }
            } else {
                null
            },
            opensDetail = item.editable,
            onClick = if (canManage && item.editable) ({ editing = item }) else null,
        )
    }

    if (creating || editing != null) {
        val target = editing
        AddOnForm(
            item = target,
            kind = kind,
            menus = menus,
            loadFailure = menusFailure,
            submitting = state.acting,
            error = actionError,
            onDelete = {
                editing = null
                deleting = target
            },
            onSubmit = { form ->
                viewModel.act(onSuccess = {
                    creating = false
                    editing = null
                }) {
                    if (kind == KindVariant) {
                        repository.saveVariant(target, form.name, form.required, form.active, form.choices, form.menuIds)
                    } else {
                        repository.saveExtra(target, form.name, form.price, form.active, form.menuIds)
                    }
                }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                creating = false
                editing = null
            },
        )
    }

    deleting?.let { item ->
        ConfirmSheet(
            title = stringResource(Res.string.addon_delete_title),
            message = stringResource(Res.string.addon_delete_message, item.name),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            onConfirm = { viewModel.act(onSuccess = { deleting = null }) { repository.delete(item) } },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
        )
    }
}

private class AddOnFormValue(
    val name: String,
    val required: Boolean,
    val active: Boolean,
    val choices: List<VariantChoice>,
    val price: Long,
    val menuIds: List<String>,
)

@Composable
private fun AddOnForm(
    item: AddOn?,
    kind: String,
    menus: List<MenuOption>,
    loadFailure: AppFailure?,
    submitting: Boolean,
    error: String?,
    onDelete: () -> Unit,
    onSubmit: (AddOnFormValue) -> Unit,
    onDismiss: () -> Unit,
) {
    var name by remember { mutableStateOf(item?.name.orEmpty()) }
    var required by remember { mutableStateOf(item?.required ?: true) }
    var active by remember { mutableStateOf(item?.active ?: true) }
    var price by remember { mutableStateOf(item?.price) }
    // Id pilihan lama ikut dikirim agar tidak dianggap pilihan baru dan riwayatnya tetap tersambung.
    val choices = remember { mutableStateListOf<VariantChoice>().apply { item?.choices?.let { addAll(it) } } }
    var selectedMenus by remember { mutableStateOf(item?.menuIds?.toSet().orEmpty()) }
    val validChoices = choices.filter { it.name.isNotBlank() }
    val canSubmit = name.isNotBlank() && if (kind == KindVariant) validChoices.isNotEmpty() else price != null

    FormSheet(
        title = stringResource(if (item == null) Res.string.addon_form_add else Res.string.addon_form_edit),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = {
            onSubmit(AddOnFormValue(name, required, active, validChoices, price ?: 0L, selectedMenus.toList()))
        },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = canSubmit,
        invalidMessage = stringResource(if (kind == KindVariant) Res.string.addon_variant_invalid else Res.string.addon_extra_invalid),
        error = error ?: loadFailure?.let { failureText(it) },
    ) {
        AppTextField(value = name, onValueChange = { name = it }, label = stringResource(Res.string.common_name))
        if (kind == KindVariant) {
            ToggleSwitch(
                label = stringResource(Res.string.addon_required),
                checked = required,
                onCheckedChange = { required = it },
            )
            TextListEditor(
                label = stringResource(Res.string.addon_choices),
                values = choices.map { it.name },
                onChange = { index, value -> choices[index] = VariantChoice(choices[index].id, value, choices[index].active, choices[index].color) },
                onAdd = { choices.add(VariantChoice(null, "", true)) },
                onRemove = { choices.removeAt(it) },
                addLabel = stringResource(Res.string.addon_choice_add),
                removeDescription = stringResource(Res.string.addon_choice_remove),
                enabled = !submitting,
            )
        } else {
            MoneyField(
                amount = price,
                onAmountChange = { price = it },
                label = stringResource(Res.string.addon_price),
            )
        }
        MultiChoiceFlow(
            label = stringResource(Res.string.addon_menus),
            options = menus.map { it.name },
            selected = menus.indices.filter { menus[it].id in selectedMenus }.toSet(),
            onToggle = { index ->
                val id = menus[index].id
                selectedMenus = if (id in selectedMenus) selectedMenus - id else selectedMenus + id
            },
        )
        if (item != null) {
            ToggleSwitch(
                label = stringResource(Res.string.common_active),
                checked = active,
                onCheckedChange = { active = it },
            )
            SecondaryButton(
                text = stringResource(Res.string.common_delete),
                onClick = onDelete,
                tone = ButtonTone.Danger,
                enabled = !submitting,
            )
        }
    }
}
