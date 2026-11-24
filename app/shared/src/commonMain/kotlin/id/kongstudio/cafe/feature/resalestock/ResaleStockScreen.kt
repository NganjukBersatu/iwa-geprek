package id.kongstudio.cafe.feature.resalestock

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_resale_stock
import id.kongstudio.cafe.resources.resale_count_cancel
import id.kongstudio.cafe.resources.resale_count_confirm_message
import id.kongstudio.cafe.resources.resale_count_confirm_title
import id.kongstudio.cafe.resources.resale_count_done
import id.kongstudio.cafe.resources.resale_count_filled
import id.kongstudio.cafe.resources.resale_count_intro
import id.kongstudio.cafe.resources.resale_count_problem_none
import id.kongstudio.cafe.resources.resale_count_real
import id.kongstudio.cafe.resources.resale_count_save
import id.kongstudio.cafe.resources.resale_count_start
import id.kongstudio.cafe.resources.resale_empty
import id.kongstudio.cafe.resources.resale_filter_adjustment
import id.kongstudio.cafe.resources.resale_filter_receipt
import id.kongstudio.cafe.resources.resale_filter_stock
import id.kongstudio.cafe.resources.resale_hint
import id.kongstudio.cafe.resources.resale_search
import id.kongstudio.cafe.resources.resale_status_low
import id.kongstudio.cafe.resources.resale_status_out
import id.kongstudio.cafe.resources.stock_count_note
import id.kongstudio.cafe.resources.stock_count_problem_invalid
import id.kongstudio.cafe.resources.stock_movement_by
import id.kongstudio.cafe.resources.stock_movements_empty
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.productcard.BlockedLabel
import id.kongstudio.cafe.ui.component.productcard.BlockedTone
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.SortKey
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.resourcelist.timeSortOptions
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.movementdetailsheet.MovementDetailSheet
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.filter_recorded_by
import id.kongstudio.cafe.feature.periods.BranchPeriodsViewModel
import id.kongstudio.cafe.feature.periods.periodDateRange
import id.kongstudio.cafe.ui.component.signedquantity.SignedQuantityText
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import org.jetbrains.compose.resources.stringResource

/** Stok Barang Jual-Ulang di tablet: jumlah saja, tanpa harga; semua tombolnya hanya muncul untuk peran yang berhak. */
@Composable
internal fun ResaleStockScreen(
    viewModel: PagedListViewModel<ResaleRow>,
    repository: ResaleStockRepository,
    count: ResaleCountViewModel,
    userChoices: UserChoiceRepository,
    access: UserAccess,
    periods: BranchPeriodsViewModel,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val today = BusinessDay.today()
    val periodRange = periodDateRange(viewModel, periods, today)
    val recorder = userFilter(viewModel, stringResource(Res.string.filter_recorded_by), userChoices)
    val counting by count.state.collectAsState()
    var editing by remember { mutableStateOf<ResaleItem?>(null) }
    var viewing by remember { mutableStateOf<ResaleMovement?>(null) }

    val canReceive = access.allows(Permission.StockReceive)
    val canAdjust = access.allows(Permission.StockAdjust)
    val canCount = access.allows(Permission.StockCount)
    val canSeeHistory = access.allows(Permission.StockView, Permission.StockReceive, Permission.StockAdjust)
    val actions = buildList {
        if (canReceive) add(ResaleAction.Receive)
        if (canAdjust) {
            add(ResaleAction.Increase)
            add(ResaleAction.Decrease)
        }
    }
    val onStockTab = state.filter == FilterStock
    val actionError = state.actionFailure?.let { failureText(it) }

    val filters = buildList {
        add(ResourceFilter(FilterStock, stringResource(Res.string.resale_filter_stock)))
        if (canSeeHistory) {
            add(ResourceFilter(FilterReceipt, stringResource(Res.string.resale_filter_receipt)))
            add(ResourceFilter(FilterAdjustment, stringResource(Res.string.resale_filter_adjustment)))
        }
    }

    ResourceList(
        title = stringResource(Res.string.nav_resale_stock),
        items = state.items,
        page = state.page,
        pageCount = viewModel.pageCount,
        total = state.total,
        pageSize = viewModel.pageSize,
        onPageChange = viewModel::setPage,
        loading = state.loading,
        failure = state.failure,
        onRetry = viewModel::reload,
        emptyText = stringResource(if (onStockTab) Res.string.resale_empty else Res.string.stock_movements_empty),
        modifier = modifier,
        searchLabel = if (onStockTab) stringResource(Res.string.resale_search) else null,
        query = state.query,
        onQueryChange = viewModel::setQuery,
        tabs = if (filters.size > 1) filters else emptyList(),
        selectedTab = state.filter,
        onTabChange = {
            count.cancel()
            viewModel.setFilter(it, if (it == FilterStock) SortKey.NameAsc else SortKey.Newest)
        },
        // Pencatat dan tanggal hanya menyaring riwayat; tab Stok selalu menampilkan stok saat ini.
        pickers = if (onStockTab) emptyList() else listOf(recorder),
        dateRange = periodRange.takeIf { !onStockTab },
        sortLabel = sortLabel(),
        sortOptions = if (onStockTab) nameSortOptions() else timeSortOptions() + nameSortOptions(),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
        actionError = actionError.takeIf { editing == null },
        summary = if (onStockTab) {
            { StockSummary(count = count, counting = counting, canCount = canCount, canWrite = actions.isNotEmpty()) }
        } else {
            null
        },
    ) { row ->
        when (row) {
            is ResaleRow.Item -> ItemRow(
                item = row.value,
                counting = counting.counting,
                typed = counting.typed[row.value.menuItemId].orEmpty(),
                onType = { count.type(row.value.menuItemId, it) },
                onClick = if (actions.isNotEmpty() && !counting.counting) {
                    {
                        viewModel.clearActionFailure()
                        editing = row.value
                    }
                } else {
                    null
                },
            )
            is ResaleRow.Movement -> MovementRow(row.value, onOpen = { viewing = row.value })
        }
    }

    viewing?.let { movement ->
        MovementDetailSheet(
            title = movement.menuItemName,
            quantity = StockQuantity.signed(movement.qty, movement.unit),
            cause = null,
            note = movement.note,
            userName = movement.userName,
            createdAt = movement.createdAt,
            onDismiss = { viewing = null },
        )
    }

    editing?.let { item ->
        ResaleEntryForm(
            item = item,
            actions = actions,
            submitting = state.acting,
            error = actionError,
            onSubmit = { action, qty, note ->
                viewModel.act(onSuccess = { editing = null }) {
                    when (action) {
                        ResaleAction.Receive -> repository.receive(item.menuItemId, qty, note)
                        ResaleAction.Increase -> repository.adjust(item.menuItemId, qty, note)
                        ResaleAction.Decrease -> repository.adjust(item.menuItemId, "-$qty", note)
                    }
                }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                editing = null
            },
        )
    }

    if (counting.confirming) {
        ConfirmSheet(
            title = stringResource(Res.string.resale_count_confirm_title),
            message = stringResource(Res.string.resale_count_confirm_message, counting.filled),
            confirmLabel = stringResource(Res.string.resale_count_save),
            onConfirm = count::close,
            onDismiss = count::dismissConfirm,
        )
    }
}

@Composable
private fun StockSummary(count: ResaleCountViewModel, counting: ResaleCountState, canCount: Boolean, canWrite: Boolean) {
    val colors = AppTheme.colors
    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        if (!counting.counting) {
            if (canWrite) BasicText(text = stringResource(Res.string.resale_hint), style = AppTheme.typography.caption.copy(color = colors.contentMuted))
            counting.result?.let {
                BasicText(text = stringResource(Res.string.resale_count_done, it.counted, it.adjusted), style = AppTheme.typography.label.copy(color = colors.primary))
            }
            if (canCount) SecondaryButton(text = stringResource(Res.string.resale_count_start), onClick = count::start)
            return@Column
        }
        BasicText(text = stringResource(Res.string.resale_count_intro), style = AppTheme.typography.caption.copy(color = colors.contentMuted))
        AppTextField(value = counting.note, onValueChange = count::setNote, label = stringResource(Res.string.stock_count_note))
        BasicText(text = stringResource(Res.string.resale_count_filled, counting.filled), style = AppTheme.typography.label.copy(color = colors.content))
        when (counting.problem) {
            ResaleCountProblem.NoLines -> Problem(stringResource(Res.string.resale_count_problem_none))
            ResaleCountProblem.Invalid -> Problem(stringResource(Res.string.stock_count_problem_invalid))
            ResaleCountProblem.None -> Unit
        }
        counting.closeFailure?.let { Problem(failureText(it)) }
        PrimaryButton(text = stringResource(Res.string.resale_count_save), onClick = count::askClose, enabled = !counting.closing)
        SecondaryButton(text = stringResource(Res.string.resale_count_cancel), onClick = count::cancel, tone = ButtonTone.Cancel)
    }
}

@Composable
private fun ItemRow(item: ResaleItem, counting: Boolean, typed: String, onType: (String) -> Unit, onClick: (() -> Unit)?) {
    Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
        // Susunan sama dengan Daftar Bahan: ikon di kiri, stok ditonjolkan di kanan, chevron bila baris bisa dibuka.
        ListRow(
            title = item.name,
            leading = { IconBadge(AppIcons.Tag) },
            trailing = {
                AppText(
                    text = StockQuantity.withUnit(item.stock, item.unit),
                    role = TextRole.Title,
                    color = when (item.status) {
                        ResaleStatus.Out -> AppTheme.colors.danger
                        ResaleStatus.Low -> AppTheme.colors.warning
                        ResaleStatus.Safe -> AppTheme.colors.content
                    },
                )
            },
            opensDetail = true,
            badge = when (item.status) {
                ResaleStatus.Out -> {
                    { BlockedLabel(text = stringResource(Res.string.resale_status_out), tone = BlockedTone.Danger) }
                }
                ResaleStatus.Low -> {
                    { BlockedLabel(text = stringResource(Res.string.resale_status_low), tone = BlockedTone.Warning) }
                }
                ResaleStatus.Safe -> null
            },
            onClick = onClick,
        )
        if (counting) {
            QuantityField(value = typed, onValueChange = onType, label = stringResource(Res.string.resale_count_real), unit = item.unit)
        }
    }
}

@Composable
private fun MovementRow(movement: ResaleMovement, onOpen: () -> Unit) {
    val written = DateTimeFormat.stamp(movement.createdAt)?.let { whenLabel(it) }.orEmpty()
    // Susunan sama dengan riwayat Rusak dan RnD: jumlah bertanda di kanan, merah bila berkurang.
    ListRow(
        title = movement.menuItemName,
        caption = movement.note,
        footnote = stringResource(Res.string.stock_movement_by, movement.userName.orEmpty(), written).trim(' ', '·'),
        trailing = { SignedQuantityText(qty = movement.qty, unit = movement.unit) },
        onClick = onOpen,
        opensDetail = true,
    )
}

@Composable
private fun Problem(text: String) {
    BasicText(text = text, style = AppTheme.typography.caption.copy(color = AppTheme.colors.danger))
}
