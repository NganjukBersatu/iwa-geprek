package id.kongstudio.cafe.feature.promotions

import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.resources.promo_form_invalid
import id.kongstudio.cafe.resources.common_active
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_from
import id.kongstudio.cafe.resources.common_inactive
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.common_to
import id.kongstudio.cafe.resources.nav_promotions
import id.kongstudio.cafe.resources.promo_activation
import id.kongstudio.cafe.resources.promo_activation_auto
import id.kongstudio.cafe.resources.promo_activation_manual
import id.kongstudio.cafe.resources.promo_add
import id.kongstudio.cafe.resources.promo_delete_message
import id.kongstudio.cafe.resources.promo_delete_title
import id.kongstudio.cafe.resources.promo_description
import id.kongstudio.cafe.resources.promo_discount
import id.kongstudio.cafe.resources.promo_empty
import id.kongstudio.cafe.resources.promo_form_add
import id.kongstudio.cafe.resources.promo_form_edit
import id.kongstudio.cafe.resources.promo_image_url
import id.kongstudio.cafe.resources.promo_info
import id.kongstudio.cafe.resources.promo_min_spend
import id.kongstudio.cafe.resources.promo_products
import id.kongstudio.cafe.resources.promo_scope
import id.kongstudio.cafe.resources.promo_scope_basic
import id.kongstudio.cafe.resources.promo_scope_product
import id.kongstudio.cafe.resources.promo_scope_total
import id.kongstudio.cafe.resources.promo_title
import id.kongstudio.cafe.resources.promo_type
import id.kongstudio.cafe.resources.promo_type_amount
import id.kongstudio.cafe.resources.promo_type_percent
import id.kongstudio.cafe.resources.promo_value
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.daterangefields.DateRangeFields
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.multichoiceflow.MultiChoiceFlow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.ui.Alignment
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.badge.ScopedActiveBadge
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun PromotionScreen(
    viewModel: PagedListViewModel<Promotion>,
    repository: PromotionRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var menus by remember { mutableStateOf<List<PromotionMenu>>(emptyList()) }
    var menusFailure by remember { mutableStateOf<AppFailure?>(null) }
    var creating by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<Promotion?>(null) }
    var deleting by remember { mutableStateOf<Promotion?>(null) }
    val kind = state.filter.ifEmpty { KindDiscount }
    val canManage = access.allows(Permission.PromoManage)
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
        ResourceFilter(KindDiscount, stringResource(Res.string.promo_discount)),
        ResourceFilter(KindInfo, stringResource(Res.string.promo_info)),
    )

    ResourceList(
        title = stringResource(Res.string.nav_promotions),
        items = state.items,
        page = 0,
        pageCount = 1,
        total = state.items.size,
        pageSize = state.items.size.coerceAtLeast(1),
        onPageChange = {},
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.promo_empty),
        modifier = modifier,
        tabs = filters,
        selectedTab = kind,
        onTabChange = viewModel::setFilter,
        addLabel = stringResource(Res.string.promo_add).takeIf { canManage },
        onAdd = { creating = true }.takeIf { canManage },
        actionError = actionError.takeIf { !creating && editing == null && deleting == null },
    ) { promo ->
        ListRow(
            title = promo.title,
            caption = "${longDateLabel(promo.from)} – ${longDateLabel(promo.to)}",
            // Saklar sudah menyatakan aktif atau tidak; lencana hanya untuk yang tidak berhak mengubahnya.
            badge = if (canManage && promo.editable) null else ({ ScopedActiveBadge(promo.active, allBranches = !promo.editable) }),
            leading = { IconBadge(AppIcons.Discount) },
            trailing = {
                Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md), verticalAlignment = Alignment.CenterVertically) {
                    if (promo.kind == KindDiscount) AppText(text = discountText(promo), role = TextRole.Title)
                    if (canManage && promo.editable) {
                        ToggleSwitch(
                            label = "",
                            accessibleName = stringResource(Res.string.common_active),
                            checked = promo.active,
                            onCheckedChange = { viewModel.act { repository.toggle(promo) } },
                        )
                    }
                }
            },
            opensDetail = promo.editable,
            onClick = if (canManage && promo.editable) ({ editing = promo }) else null,
        )
    }

    if (creating || editing != null) {
        val target = editing
        PromotionFormSheet(
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
                }) { repository.save(target, kind, form) }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                creating = false
                editing = null
            },
        )
    }

    deleting?.let { promo ->
        ConfirmSheet(
            title = stringResource(Res.string.promo_delete_title),
            message = stringResource(Res.string.promo_delete_message, promo.title),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            onConfirm = { viewModel.act(onSuccess = { deleting = null }) { repository.delete(promo) } },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
        )
    }
}

@Composable
private fun discountText(promo: Promotion): String = when (promo.type) {
    DiscountType.Percent -> "${promo.value}%"
    DiscountType.Amount -> formatRupiah(promo.value)
}

@Composable
private fun PromotionFormSheet(
    item: Promotion?,
    kind: String,
    menus: List<PromotionMenu>,
    loadFailure: AppFailure?,
    submitting: Boolean,
    error: String?,
    onDelete: () -> Unit,
    onSubmit: (PromotionForm) -> Unit,
    onDismiss: () -> Unit,
) {
    val today = remember { DateTimeFormat.todayWib() }
    var title by remember { mutableStateOf(item?.title.orEmpty()) }
    var description by remember { mutableStateOf(item?.description.orEmpty()) }
    var scope by remember { mutableStateOf(item?.scope ?: DiscountScope.Basic) }
    var type by remember { mutableStateOf(item?.type ?: DiscountType.Percent) }
    var valueText by remember { mutableStateOf(item?.value?.takeIf { it > 0 }?.toString().orEmpty()) }
    var minText by remember { mutableStateOf(item?.minSpend?.toString().orEmpty()) }
    var activation by remember { mutableStateOf(item?.activation ?: Activation.Auto) }
    var imageUrl by remember { mutableStateOf(item?.imageUrl.orEmpty()) }
    var from by remember { mutableStateOf(item?.from ?: today) }
    var to by remember { mutableStateOf(item?.to ?: today) }
    var active by remember { mutableStateOf(item?.active ?: true) }
    var selectedMenus by remember { mutableStateOf(item?.productIds?.toSet().orEmpty()) }
    val value = valueText.filter { it.isDigit() }.toLongOrNull()
    val isDiscount = kind == KindDiscount
    val scopes = DiscountScope.entries
    val types = DiscountType.entries
    val activations = Activation.entries

    FormSheet(
        title = stringResource(if (item == null) Res.string.promo_form_add else Res.string.promo_form_edit),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = {
            onSubmit(
                PromotionForm(
                    title = title,
                    description = description,
                    scope = scope,
                    type = type,
                    value = value ?: 0L,
                    productIds = selectedMenus.toList(),
                    minSpend = minText.filter { it.isDigit() }.toLongOrNull(),
                    activation = activation,
                    imageUrl = imageUrl,
                    from = from,
                    to = to,
                    active = active,
                ),
            )
        },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = title.isNotBlank() && (!isDiscount || (value != null && value > 0)),
        invalidMessage = stringResource(Res.string.promo_form_invalid),
        error = error ?: loadFailure?.let { failureText(it) },
    ) {
        AppTextField(value = title, onValueChange = { title = it }, label = stringResource(Res.string.promo_title))
        AppTextField(
            value = description,
            onValueChange = { description = it },
            label = stringResource(Res.string.promo_description),
        )
        if (isDiscount) {
            ChoiceGroup(
                label = stringResource(Res.string.promo_scope),
                options = scopes.map { scopeLabel(it) },
                selectedIndex = scopes.indexOf(scope),
                onSelect = { scope = scopes[it] },
            )
            ChoiceGroup(
                label = stringResource(Res.string.promo_type),
                options = types.map { typeLabel(it) },
                selectedIndex = types.indexOf(type),
                onSelect = { type = types[it] },
            )
            if (type == DiscountType.Amount) {
                MoneyField(
                    amount = value,
                    onAmountChange = { valueText = it?.toString().orEmpty() },
                    label = stringResource(Res.string.promo_value),
                )
            } else {
                AppTextField(
                    value = valueText,
                    onValueChange = { valueText = it.filter { c -> c.isDigit() } },
                    label = stringResource(Res.string.promo_value),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                )
            }
            if (scope == DiscountScope.Total) {
                MoneyField(
                    amount = minText.filter { it.isDigit() }.toLongOrNull(),
                    onAmountChange = { minText = it?.toString().orEmpty() },
                    label = stringResource(Res.string.promo_min_spend),
                )
            }
            if (scope == DiscountScope.Product) {
                MultiChoiceFlow(
                    label = stringResource(Res.string.promo_products),
                    options = menus.map { it.name },
                    selected = menus.indices.filter { menus[it].id in selectedMenus }.toSet(),
                    onToggle = { index ->
                        val id = menus[index].id
                        selectedMenus = if (id in selectedMenus) selectedMenus - id else selectedMenus + id
                    },
                )
            }
            ChoiceGroup(
                label = stringResource(Res.string.promo_activation),
                options = activations.map { activationLabel(it) },
                selectedIndex = activations.indexOf(activation),
                onSelect = { activation = activations[it] },
            )
        } else {
            AppTextField(
                value = imageUrl,
                onValueChange = { imageUrl = it },
                label = stringResource(Res.string.promo_image_url),
            )
        }
        DateRangeFields(
            from = from,
            to = to,
            today = today,
            fromLabel = stringResource(Res.string.common_from),
            toLabel = stringResource(Res.string.common_to),
            onChange = { newFrom, newTo ->
                from = newFrom
                to = newTo
            },
            enabled = !submitting,
        )
        ToggleSwitch(
            label = stringResource(Res.string.common_active),
            checked = active,
            onCheckedChange = { active = it },
        )
        if (item != null) {
            SecondaryButton(
                text = stringResource(Res.string.common_delete),
                onClick = onDelete,
                tone = ButtonTone.Danger,
                enabled = !submitting,
            )
        }
    }
}

@Composable
private fun scopeLabel(scope: DiscountScope): String = stringResource(
    when (scope) {
        DiscountScope.Basic -> Res.string.promo_scope_basic
        DiscountScope.Product -> Res.string.promo_scope_product
        DiscountScope.Total -> Res.string.promo_scope_total
    },
)

@Composable
private fun typeLabel(type: DiscountType): String = stringResource(
    when (type) {
        DiscountType.Percent -> Res.string.promo_type_percent
        DiscountType.Amount -> Res.string.promo_type_amount
    },
)

@Composable
private fun activationLabel(activation: Activation): String = stringResource(
    when (activation) {
        Activation.Auto -> Res.string.promo_activation_auto
        Activation.Manual -> Res.string.promo_activation_manual
    },
)
