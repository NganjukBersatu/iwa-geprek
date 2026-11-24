package id.kongstudio.cafe.feature.ordernotes

import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.filter_created_by
import id.kongstudio.cafe.resources.order_note_created_by
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.order_note_name_required
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_name
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.nav_order_notes
import id.kongstudio.cafe.resources.order_note_add
import id.kongstudio.cafe.resources.order_note_delete_message
import id.kongstudio.cafe.resources.order_note_delete_title
import id.kongstudio.cafe.resources.order_note_empty
import id.kongstudio.cafe.resources.order_note_form_add
import id.kongstudio.cafe.resources.order_note_form_edit
import id.kongstudio.cafe.resources.order_note_in_use
import id.kongstudio.cafe.resources.order_note_search
import id.kongstudio.cafe.resources.order_note_shared
import id.kongstudio.cafe.resources.order_note_used
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Catatan pesanan satu cabang: tambah, ganti nama, dan hapus yang belum terpakai; catatan umum lama hanya terbaca. */
@Composable
internal fun OrderNoteScreen(
    viewModel: PagedListViewModel<OrderNote>,
    repository: OrderNoteRepository,
    userChoices: UserChoiceRepository,
    access: UserAccess,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val creator = userFilter(viewModel, stringResource(Res.string.filter_created_by), userChoices)
    var creating by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<OrderNote?>(null) }
    var deleting by remember { mutableStateOf<OrderNote?>(null) }
    val canManage = access.allows(Permission.ReferenceManage)
    val actionError = state.actionFailure?.let { failureText(it) }

    ResourceList(
        title = stringResource(Res.string.nav_order_notes),
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(Res.string.order_note_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.order_note_search),
        query = state.query,
        onQueryChange = viewModel::setQuery,
        pickers = listOf(creator),
        sortLabel = sortLabel(),
        sortOptions = nameSortOptions(),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
        addLabel = stringResource(Res.string.order_note_add).takeIf { canManage },
        onAdd = { creating = true }.takeIf { canManage },
        actionError = actionError.takeIf { !creating && editing == null && deleting == null },
    ) { note ->
        ListRow(
            title = note.name,
            detail = stringResource(Res.string.order_note_used, note.usedBy),
            caption = listOfNotNull(
                stringResource(Res.string.order_note_shared).takeIf { note.shared },
                note.createdBy?.let { stringResource(Res.string.order_note_created_by, it) },
            ).joinToString(" · ").ifEmpty { null },
            leading = { IconBadge(AppIcons.Notes) },
            opensDetail = true,
            onClick = if (canManage && !note.shared) ({ editing = note }) else null,
        )
    }

    if (creating || editing != null) {
        val target = editing
        NoteForm(
            note = target,
            submitting = state.acting,
            error = actionError,
            onDelete = {
                editing = null
                deleting = target
            },
            onSubmit = { name ->
                viewModel.act(onSuccess = {
                    creating = false
                    editing = null
                }) {
                    if (target == null) repository.create(name) else repository.rename(target, name)
                }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                creating = false
                editing = null
            },
        )
    }

    deleting?.let { note ->
        ConfirmSheet(
            title = stringResource(Res.string.order_note_delete_title),
            message = stringResource(Res.string.order_note_delete_message, note.name),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            onConfirm = { viewModel.act(onSuccess = { deleting = null }) { repository.delete(note) } },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
        )
    }
}

@Composable
private fun NoteForm(
    note: OrderNote?,
    submitting: Boolean,
    error: String?,
    onDelete: () -> Unit,
    onSubmit: (name: String) -> Unit,
    onDismiss: () -> Unit,
) {
    var name by remember { mutableStateOf(note?.name.orEmpty()) }
    val inUse = (note?.usedBy ?: 0) > 0

    FormSheet(
        title = stringResource(if (note == null) Res.string.order_note_form_add else Res.string.order_note_form_edit),
        submitLabel = stringResource(Res.string.common_save),
        onSubmit = { onSubmit(name) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = name.isNotBlank(),
        invalidMessage = stringResource(Res.string.order_note_name_required),
        error = error,
    ) {
        AppTextField(value = name, onValueChange = { name = it }, label = stringResource(Res.string.common_name))
        if (note != null) {
            if (inUse) {
                BasicText(
                    text = stringResource(Res.string.order_note_in_use, note.usedBy),
                    style = AppTheme.typography.caption.copy(color = AppTheme.colors.contentMuted),
                )
            }
            SecondaryButton(
                text = stringResource(Res.string.common_delete),
                onClick = onDelete,
                tone = ButtonTone.Danger,
                enabled = !submitting && !inUse,
            )
        }
    }
}
