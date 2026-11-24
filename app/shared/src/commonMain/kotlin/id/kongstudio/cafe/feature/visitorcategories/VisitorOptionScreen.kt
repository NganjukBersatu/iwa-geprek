package id.kongstudio.cafe.feature.visitorcategories

import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.visitor_name_required
import id.kongstudio.cafe.resources.common_active
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_inactive
import id.kongstudio.cafe.resources.common_name
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.nav_visitor_categories
import id.kongstudio.cafe.resources.visitor_add
import id.kongstudio.cafe.resources.visitor_asks_gender
import id.kongstudio.cafe.resources.visitor_category
import id.kongstudio.cafe.resources.visitor_delete_in_use
import id.kongstudio.cafe.resources.visitor_delete_message
import id.kongstudio.cafe.resources.visitor_delete_title
import id.kongstudio.cafe.resources.visitor_empty
import id.kongstudio.cafe.resources.visitor_form_add
import id.kongstudio.cafe.resources.visitor_form_edit
import id.kongstudio.cafe.resources.visitor_gender
import id.kongstudio.cafe.resources.visitor_used
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun VisitorOptionScreen(
    viewModel: PagedListViewModel<VisitorOption>,
    repository: VisitorOptionRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var creating by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<VisitorOption?>(null) }
    var deleting by remember { mutableStateOf<VisitorOption?>(null) }
    val canManage = access.allows(Permission.VisitorManage)
    val section = state.filter.ifEmpty { SectionCategory }
    val actionError = state.actionFailure?.let { failureText(it) }
    val filters = listOf(
        ResourceFilter(SectionCategory, stringResource(Res.string.visitor_category)),
        ResourceFilter(SectionGender, stringResource(Res.string.visitor_gender)),
    )

    ResourceList(
        title = stringResource(Res.string.nav_visitor_categories),
        items = state.items,
        page = 0,
        pageCount = 1,
        total = state.items.size,
        pageSize = state.items.size.coerceAtLeast(1),
        onPageChange = {},
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.visitor_empty),
        modifier = modifier,
        tabs = filters,
        selectedTab = section,
        onTabChange = viewModel::setFilter,
        addLabel = stringResource(Res.string.visitor_add).takeIf { canManage },
        onAdd = { creating = true }.takeIf { canManage },
        actionError = actionError.takeIf { !creating && editing == null && deleting == null },
    ) { option ->
        ListRow(
            title = option.name,
            detail = stringResource(Res.string.visitor_used, option.usedBy),
            caption = if (option.asksGender) stringResource(Res.string.visitor_asks_gender) else null,
            footnote = stringResource(if (option.active) Res.string.common_active else Res.string.common_inactive),
            leading = { IconBadge(AppIcons.Category) },
            onClick = if (canManage) ({ editing = option }) else null,
        )
    }

    if (creating || editing != null) {
        val target = editing
        OptionForm(
            option = target,
            section = section,
            submitting = state.acting,
            error = actionError,
            canDelete = target != null,
            onDelete = {
                editing = null
                deleting = target
            },
            onSubmit = { name, asksGender, active ->
                viewModel.act(onSuccess = {
                    creating = false
                    editing = null
                }) {
                    if (target == null) {
                        repository.create(section, name, asksGender)
                    } else {
                        repository.update(target, name, asksGender, active)
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

    deleting?.let { option ->
        ConfirmSheet(
            title = stringResource(Res.string.visitor_delete_title),
            message = if (option.usedBy > 0) {
                stringResource(Res.string.visitor_delete_in_use, option.name, option.usedBy)
            } else {
                stringResource(Res.string.visitor_delete_message, option.name)
            },
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            // Pilihan yang sudah dipakai pesanan ditolak server; hanya bisa dinonaktifkan.
            confirmEnabled = option.usedBy == 0,
            onConfirm = { viewModel.act(onSuccess = { deleting = null }) { repository.delete(option) } },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
        )
    }
}

@Composable
private fun OptionForm(
    option: VisitorOption?,
    section: String,
    submitting: Boolean,
    error: String?,
    canDelete: Boolean,
    onDelete: () -> Unit,
    onSubmit: (name: String, asksGender: Boolean, active: Boolean) -> Unit,
    onDismiss: () -> Unit,
) {
    var name by remember { mutableStateOf(option?.name.orEmpty()) }
    var asksGender by remember { mutableStateOf(option?.asksGender ?: false) }
    var active by remember { mutableStateOf(option?.active ?: true) }

    FormSheet(
        title = stringResource(if (option == null) Res.string.visitor_form_add else Res.string.visitor_form_edit),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = { onSubmit(name, asksGender, active) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = name.isNotBlank(),
        invalidMessage = stringResource(Res.string.visitor_name_required),
        error = error,
    ) {
        AppTextField(value = name, onValueChange = { name = it }, label = stringResource(Res.string.common_name))
        if (section == SectionCategory) {
            ToggleSwitch(
                label = stringResource(Res.string.visitor_asks_gender),
                checked = asksGender,
                onCheckedChange = { asksGender = it },
            )
        }
        if (option != null) {
            ToggleSwitch(
                label = stringResource(Res.string.common_active),
                checked = active,
                onCheckedChange = { active = it },
            )
        }
        if (canDelete) {
            SecondaryButton(
                text = stringResource(Res.string.common_delete),
                onClick = onDelete,
                tone = ButtonTone.Danger,
                enabled = !submitting,
            )
        }
    }
}
