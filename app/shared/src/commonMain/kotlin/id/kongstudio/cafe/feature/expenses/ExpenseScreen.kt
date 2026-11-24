package id.kongstudio.cafe.feature.expenses

import id.kongstudio.cafe.feature.admin.ListParam
import id.kongstudio.cafe.feature.periods.BranchPeriodsViewModel
import id.kongstudio.cafe.feature.periods.periodDateRange
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.isQuantityTyping
import id.kongstudio.cafe.core.format.quantityOf
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.ChoicePage
import id.kongstudio.cafe.feature.admin.ChoicePages
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.admin.rememberChoicePages
import id.kongstudio.cafe.feature.deposits.DayCheck
import id.kongstudio.cafe.feature.deposits.DepositedDayNotice
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.common_cancel
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_edit
import id.kongstudio.cafe.resources.common_recorded_by
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.resources.common_time
import id.kongstudio.cafe.resources.expense_add
import id.kongstudio.cafe.resources.expense_add_row
import id.kongstudio.cafe.resources.expense_amount
import id.kongstudio.cafe.resources.back_to_expenses
import id.kongstudio.cafe.resources.expense_form_invalid
import id.kongstudio.cafe.resources.expense_form_wait
import id.kongstudio.cafe.resources.expense_row_removed
import id.kongstudio.cafe.resources.expense_row_undo
import id.kongstudio.cafe.resources.filter_recorded_by
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.resources.expense_branch
import id.kongstudio.cafe.resources.expense_buyer
import id.kongstudio.cafe.resources.expense_buyer_of
import id.kongstudio.cafe.resources.expense_buyer_self
import id.kongstudio.cafe.resources.expense_delete_message
import id.kongstudio.cafe.resources.expense_delete_title
import id.kongstudio.cafe.resources.expense_detail_title
import id.kongstudio.cafe.resources.expense_empty
import id.kongstudio.cafe.resources.expense_form_add
import id.kongstudio.cafe.resources.expense_form_edit
import id.kongstudio.cafe.resources.expense_ingredient
import id.kongstudio.cafe.resources.expense_maybe_ingredient
import id.kongstudio.cafe.resources.expense_name
import id.kongstudio.cafe.resources.expense_no_buyer
import id.kongstudio.cafe.resources.expense_no_ingredient
import id.kongstudio.cafe.resources.expense_not_ingredient
import id.kongstudio.cafe.resources.expense_note
import id.kongstudio.cafe.resources.expense_proof
import id.kongstudio.cafe.resources.expense_quantity
import id.kongstudio.cafe.resources.expense_quantity_of
import id.kongstudio.cafe.resources.expense_read_done
import id.kongstudio.cafe.resources.expense_read_empty
import id.kongstudio.cafe.resources.expense_read_from
import id.kongstudio.cafe.resources.expense_read_hint
import id.kongstudio.cafe.resources.expense_read_matched
import id.kongstudio.cafe.resources.expense_read_receipt
import id.kongstudio.cafe.resources.expense_remove_row
import id.kongstudio.cafe.resources.expense_rows_total
import id.kongstudio.cafe.resources.expense_search
import id.kongstudio.cafe.resources.expense_search_buyer
import id.kongstudio.cafe.resources.expense_search_ingredient
import id.kongstudio.cafe.resources.expense_source
import id.kongstudio.cafe.resources.expense_source_budget
import id.kongstudio.cafe.resources.expense_source_drawer
import id.kongstudio.cafe.resources.expense_source_other
import id.kongstudio.cafe.resources.expense_summary
import id.kongstudio.cafe.resources.expense_total_mismatch
import id.kongstudio.cafe.resources.expense_whole_receipt
import id.kongstudio.cafe.resources.nav_expenses
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.photofield.PhotoField
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.photoreadbutton.PhotoReadButton
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.resourcelist.timeSortOptions
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.splitpage.SplitPage
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.getString
import org.jetbrains.compose.resources.stringResource


@Composable
internal fun ExpenseScreen(
    viewModel: PagedListViewModel<ExpenseItem>,
    repository: ExpenseRepository,
    access: UserAccess,
    userChoices: UserChoiceRepository,
    periods: BranchPeriodsViewModel,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val summary by repository.summary.collectAsState()
    var editing by remember { mutableStateOf<ExpenseItem?>(null) }
    var creating by remember { mutableStateOf(false) }
    // Rincian diikuti lewat id supaya ikut terbarui saat daftar dimuat ulang; [opened] cadangan bila barisnya tidak ada di halaman ini.
    var detailId by remember { mutableStateOf<String?>(null) }
    var opened by remember { mutableStateOf<ExpenseItem?>(null) }
    var deleting by remember { mutableStateOf<ExpenseItem?>(null) }
    var dayCheck by remember { mutableStateOf<DayCheck>(DayCheck.Idle) }
    val today = BusinessDay.today()
    val actionError = state.actionFailure?.let { failureText(it) }
    val canAdd = access.allows(Permission.ExpenseRecord)
    val canChange = access.allows(Permission.ExpenseEditOwn, Permission.ExpenseEditAll)
    val detail = detailId?.let { id -> state.items.firstOrNull { it.id == id } ?: opened?.takeIf { it.id == id } }

    val filters = listOf(
        ResourceFilter("", stringResource(Res.string.common_all)),
        ResourceFilter(FundSource.Drawer.code, stringResource(Res.string.expense_source_drawer)),
        ResourceFilter(FundSource.Other.code, stringResource(Res.string.expense_source_other)),
    )
    // Server membatasi ke pencatatan sendiri tanpa izin ini, jadi penyaring hanya berguna bagi yang punya izin.
    val pickers = if (access.allows(Permission.ExpenseViewAll)) {
        listOf(userFilter(viewModel, stringResource(Res.string.filter_recorded_by), userChoices))
    } else {
        emptyList()
    }

    // Hari setoran diperiksa setiap halaman ubah, hapus, atau catat dibuka; pengeluaran baru masuk ke sesi yang berjalan.
    LaunchedEffect(creating, editing?.id, deleting?.id) {
        val ids = listOfNotNull(deleting?.id ?: editing?.id)
        if (!creating && ids.isEmpty()) {
            dayCheck = DayCheck.Idle
            return@LaunchedEffect
        }
        dayCheck = DayCheck.Checking
        dayCheck = when (val result = repository.dayStates(ids)) {
            is DeviceResult.Ok -> DayCheck.Ready(result.value)
            is DeviceResult.Failed -> DayCheck.Failed
        }
    }

    val closeForm = {
        viewModel.clearActionFailure()
        creating = false
        editing = null
    }

    when {
        creating || editing != null -> ExpenseFormPage(
            item = editing,
            submitting = state.acting,
            error = actionError,
            dayCheck = dayCheck,
            onRead = repository::readReceipt,
            onIngredients = repository::ingredients,
            onBuyers = repository::buyers,
            onCreate = { entries, source, buyer, note, proof ->
                viewModel.act(onSuccess = { creating = false }) {
                    repository.record(entries, source, buyer, note, proof).also { result ->
                        if (result is DeviceResult.Ok) {
                            // Hari bisnis pengeluaran mengikuti sesi kas, jadi rentang daftar diluaskan sampai baris yang baru disimpan ikut tampil.
                            val days = result.value.map { it.businessDay }
                            val from = state.params[ListParam.From] ?: BusinessDay.today()
                            val to = state.params[ListParam.To] ?: BusinessDay.today()
                            val low = (days + from).min()
                            val high = (days + to).max()
                            if (low != from || high != to) viewModel.setParams(ListParam.From to low, ListParam.To to high)
                        }
                    }
                }
            },
            onUpdate = { id, entry, source, buyer, note, proof ->
                viewModel.act(onSuccess = { editing = null }) {
                    repository.update(id, entry, source, buyer, note, proof).also { result -> if (result is DeviceResult.Ok) opened = result.value }
                }
            },
            onDismiss = closeForm,
            modifier = modifier,
        )
        detail != null -> ExpenseDetailPage(
            item = detail,
            canChange = canChange,
            onEdit = { editing = detail },
            onDelete = { deleting = detail },
            onBack = {
                detailId = null
                opened = null
            },
            modifier = modifier,
        )
        else -> ResourceList(
            title = stringResource(Res.string.nav_expenses),
            items = state.items,
            page = state.page,
            pageCount = viewModel.pageCount,
            total = state.total,
            pageSize = viewModel.pageSize,
            onPageChange = viewModel::setPage,
            loading = state.loading,
            failure = state.failure,
            onRetry = viewModel::reload,
            emptyText = stringResource(Res.string.expense_empty),
            modifier = modifier,
            searchLabel = stringResource(Res.string.expense_search),
            query = state.query,
            onQueryChange = viewModel::setQuery,
            filters = filters,
            selectedFilter = state.filter,
            onFilterChange = viewModel::setFilter,
            pickers = pickers,
            sortLabel = sortLabel(),
            sortOptions = timeSortOptions(newest = "-created_at", oldest = "created_at") + nameSortOptions(ascending = "item", descending = "-item"),
            selectedSort = state.sort,
            onSortChange = viewModel::setSort,
            addLabel = stringResource(Res.string.expense_add).takeIf { canAdd },
            onAdd = { creating = true }.takeIf { canAdd },
            actionError = actionError,
            dateRange = periodDateRange(viewModel, periods, today),
            summary = {
                if (!state.loading && state.failure == null) {
                    AppText(
                        text = stringResource(
                            Res.string.expense_summary,
                            state.total,
                            formatRupiah(summary.total),
                            formatRupiah(summary.fromDrawer),
                        ),
                        role = TextRole.Caption,
                        color = AppTheme.colors.contentMuted,
                    )
                }
            },
        ) { item ->
            ListRow(
                title = item.name,
                caption = listOfNotNull(item.buyer ?: item.cashier, sourceLabel(item.source)).joinToString(" · "),
                footnote = DateTimeFormat.stamp(item.createdAt)?.let { whenLabel(it) },
                leading = { IconBadge(AppIcons.Wallet) },
                trailing = { AppText(text = formatRupiah(item.amount), role = TextRole.Title, color = AppTheme.colors.content) },
                opensDetail = true,
                onClick = {
                    detailId = item.id
                    opened = item
                },
            )
        }
    }

    deleting?.let { item ->
        ConfirmSheet(
            title = stringResource(Res.string.expense_delete_title),
            message = stringResource(Res.string.expense_delete_message, item.name, formatRupiah(item.amount)),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            confirmEnabled = dayCheck !is DayCheck.Checking,
            onConfirm = {
                viewModel.act(
                    onSuccess = {
                        deleting = null
                        detailId = null
                        opened = null
                    },
                ) { repository.delete(item.id) }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = null
            },
            notice = {
                DepositedDayNotice(dayCheck)
                actionError?.let { InlineMessage(text = it) }
            },
        )
    }
}

@Composable
private fun sourceLabel(source: FundSource): String = stringResource(
    when (source) {
        FundSource.Drawer -> Res.string.expense_source_drawer
        FundSource.Other -> Res.string.expense_source_other
        FundSource.Budget -> Res.string.expense_source_budget
    },
)

/** Halaman rincian: kiri nominal merah dan isian, kanan foto nota beserta Ubah dan Hapus bagi yang berhak. */
@Composable
private fun ExpenseDetailPage(
    item: ExpenseItem,
    canChange: Boolean,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val stamp = DateTimeFormat.stamp(item.createdAt)

    SplitPage(
        title = stringResource(Res.string.expense_detail_title),
        onBack = onBack,
        backLabel = stringResource(Res.string.back_to_expenses),
        modifier = modifier,
        main = {
            AppText(text = formatRupiah(item.amount), role = TextRole.Headline, color = AppTheme.colors.content)
            DetailCard(
                rows = listOf(
                    stringResource(Res.string.expense_name) to item.name,
                    stringResource(Res.string.expense_ingredient) to item.ingredientName,
                    stringResource(Res.string.expense_quantity) to item.quantity?.let { quantity ->
                        item.unitName?.let { stringResource(Res.string.expense_quantity_of, quantity, it) } ?: quantity
                    },
                    stringResource(Res.string.expense_source) to sourceLabel(item.source),
                    stringResource(Res.string.expense_buyer) to item.buyer,
                    stringResource(Res.string.common_recorded_by) to item.cashier,
                    stringResource(Res.string.expense_branch) to item.outletName,
                    stringResource(Res.string.common_time) to stamp?.let { whenLabel(it) },
                    stringResource(Res.string.expense_note) to item.note,
                ),
            )
        },
        side = {
            item.proofUrl?.let { url ->
                RemoteImage(url = url, contentDescription = stringResource(Res.string.expense_proof))
            }
            if (canChange) {
                PrimaryButton(text = stringResource(Res.string.common_edit), onClick = onEdit)
                SecondaryButton(
                    text = stringResource(Res.string.common_delete),
                    onClick = onDelete,
                    tone = ButtonTone.Danger,
                )
            }
        },
    )
}

/** Satu baris barang nota yang diketik bebas lalu diperiksa saat disimpan, menjadi baris bahan bila [ingredient] dengan [suggestions] bahan mirip saat server belum yakin. */
private class EntryDraft(
    name: String = "",
    amount: String = "",
    ingredient: IngredientOption? = null,
    quantity: String = "",
    val suggestions: List<IngredientOption> = emptyList(),
) {
    var name by mutableStateOf(name)
    var amount by mutableStateOf(amount)
    var ingredient by mutableStateOf(ingredient)
    var quantity by mutableStateOf(quantity)
    val value: Long? get() = amount.filter { it.isDigit() }.toLongOrNull()

    /** Kosong atau nol berarti tanpa jumlah. */
    private val quantityValue: String?
        get() = ingredient?.let { quantityOf(quantity) }

    fun pick(choice: IngredientOption?) {
        ingredient = choice
        if (choice == null) quantity = "" else if (name.isBlank()) name = choice.name
    }

    fun toEntry() = ReceiptEntry(name, value ?: 0L, ingredient?.id, quantityValue)
}

private fun draftOf(item: ExpenseItem?): EntryDraft = EntryDraft(
    name = item?.name.orEmpty(),
    amount = item?.amount?.toString().orEmpty(),
    ingredient = item?.let { saved -> saved.ingredientId?.let { IngredientOption(it, saved.ingredientName ?: saved.name, saved.unitName) } },
    quantity = item?.quantity.orEmpty(),
)

private suspend fun draftsFrom(reading: ReceiptReading): List<EntryDraft> {
    val total = reading.total
    return when {
        reading.entries.isNotEmpty() -> reading.entries.map { line ->
            EntryDraft(line.name, line.amount.toString(), line.ingredient, line.quantity?.toString().orEmpty(), line.suggestions)
        }
        // Hanya total yang terbaca: satu baris untuk seluruh nota supaya jumlahnya tetap terisi.
        total != null -> listOf(EntryDraft(reading.store?.let { getString(Res.string.expense_whole_receipt, it) }.orEmpty(), total.toString()))
        else -> listOf(EntryDraft())
    }
}

@Composable
private fun ExpenseFormPage(
    item: ExpenseItem?,
    submitting: Boolean,
    error: String?,
    dayCheck: DayCheck,
    onRead: suspend (ByteArray) -> DeviceResult<ReceiptReading>,
    onIngredients: suspend (String, Int) -> DeviceResult<ChoicePage<IngredientOption>>,
    onBuyers: suspend (String, Int) -> DeviceResult<ChoicePage<BuyerOption>>,
    onCreate: (List<ReceiptEntry>, FundSource, String, String, ByteArray?) -> Unit,
    onUpdate: (String, ReceiptEntry, FundSource, String, String, ByteArray?) -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val entries = remember { mutableStateListOf(draftOf(item)) }
    val ingredients = rememberChoicePages<IngredientOption>(key = { it.id }, fetch = onIngredients)
    val buyers = rememberChoicePages<BuyerOption>(key = { it.id }, fetch = onBuyers)
    var source by remember { mutableStateOf(item?.source?.takeIf { it != FundSource.Budget } ?: FundSource.Drawer) }
    var buyer by remember { mutableStateOf(item?.buyer.orEmpty()) }
    var note by remember { mutableStateOf(item?.note.orEmpty()) }
    var photo by remember { mutableStateOf<PickedPhoto?>(null) }
    var reading by remember { mutableStateOf(false) }
    var attempted by remember { mutableStateOf(false) }
    var removedRow by remember { mutableStateOf<Pair<Int, EntryDraft>?>(null) }
    var readResult by remember { mutableStateOf<ReceiptReading?>(null) }
    var readFailure by remember { mutableStateOf<AppFailure?>(null) }
    val scope = rememberCoroutineScope()
    val sources = listOf(FundSource.Drawer, FundSource.Other)
    val rowsTotal = entries.sumOf { it.value ?: 0L }
    val printedTotal = readResult?.total

    fun read(picked: PickedPhoto) {
        photo = picked
        scope.launch {
            reading = true
            when (val result = onRead(picked.bytes)) {
                is DeviceResult.Ok -> {
                    readResult = result.value
                    readFailure = null
                    val drafts = draftsFrom(result.value)
                    entries.clear()
                    entries.addAll(drafts)
                    if (note.isBlank()) result.value.store?.let { note = it }
                }
                is DeviceResult.Failed -> {
                    readResult = null
                    readFailure = result.failure
                }
            }
            reading = false
        }
    }

    val canSubmit = !reading && dayCheck !is DayCheck.Checking && entries.isNotEmpty() && entries.all { it.name.isNotBlank() && (it.value ?: 0L) > 0L }
    val submit: () -> Unit = {
        if (item == null) {
            onCreate(entries.map { it.toEntry() }, source, buyer, note, photo?.bytes)
        } else {
            entries.firstOrNull()?.let { onUpdate(item.id, it.toEntry(), source, buyer, note, photo?.bytes) }
        }
    }

    SplitPage(
        title = stringResource(if (item == null) Res.string.expense_form_add else Res.string.expense_form_edit),
        onBack = onDismiss,
        backLabel = stringResource(Res.string.back_to_expenses),
        modifier = modifier,
        canLeave = !submitting,
        main = {
            if (item == null) {
                AppText(text = stringResource(Res.string.expense_read_hint), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                PhotoReadButton(
                    label = stringResource(Res.string.expense_read_receipt),
                    reading = reading,
                    onPicked = ::read,
                    enabled = !submitting,
                    modifier = Modifier.fillMaxWidth(),
                )
                val result = readResult
                val failure = readFailure
                when {
                    failure != null -> StatusBanner(text = failureText(failure), tone = BannerTone.Warning)
                    result != null && result.entries.isEmpty() && result.total == null ->
                        StatusBanner(text = stringResource(Res.string.expense_read_empty), tone = BannerTone.Warning)
                    result != null -> StatusBanner(
                        text = result.store?.let { stringResource(Res.string.expense_read_from, it) } ?: stringResource(Res.string.expense_read_done),
                    )
                }
                val matched = result?.entries?.count { it.ingredient != null } ?: 0
                if (matched > 0) {
                    AppText(text = stringResource(Res.string.expense_read_matched, matched), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                }
            }
            entries.forEachIndexed { index, entry ->
                EntryFields(
                    entry = entry,
                    ingredients = ingredients,
                    onRemove = if (entries.size > 1) ({ removedRow = index to entries.removeAt(index) }) else null,
                    enabled = !submitting,
                )
            }
            removedRow?.let { (position, draft) ->
                StatusBanner(
                    text = stringResource(Res.string.expense_row_removed),
                    tone = BannerTone.Info,
                    actionLabel = stringResource(Res.string.expense_row_undo),
                    onAction = {
                        entries.add(position.coerceAtMost(entries.size), draft)
                        removedRow = null
                    },
                )
            }
            if (item == null) {
                SecondaryButton(text = stringResource(Res.string.expense_add_row), onClick = { entries.add(EntryDraft()) }, enabled = !submitting)
                AppText(text = stringResource(Res.string.expense_rows_total, formatRupiah(rowsTotal)), role = TextRole.Title, color = AppTheme.colors.content)
                if (printedTotal != null && printedTotal != rowsTotal) {
                    StatusBanner(
                        text = stringResource(Res.string.expense_total_mismatch, formatRupiah(printedTotal), formatRupiah(rowsTotal)),
                        tone = BannerTone.Warning,
                    )
                }
            }
        },
        side = {
            ChoiceGroup(
                label = stringResource(Res.string.expense_source),
                options = sources.map { sourceLabel(it) },
                selectedIndex = sources.indexOf(source),
                onSelect = { source = sources[it] },
            )
            BuyerField(buyer = buyer, buyers = buyers, onChange = { buyer = it })
            AppTextField(value = note, onValueChange = { note = it }, label = stringResource(Res.string.expense_note))
            PhotoField(photo = photo, onPicked = { photo = it }, enabled = !submitting && !reading)
            DepositedDayNotice(dayCheck)
            error?.let { InlineMessage(text = it) }
            if (attempted && !canSubmit) {
                InlineMessage(text = stringResource(if (reading || dayCheck is DayCheck.Checking) Res.string.expense_form_wait else Res.string.expense_form_invalid))
            }
            PrimaryButton(text = stringResource(Res.string.common_save), onClick = { if (canSubmit) submit() else attempted = true }, enabled = !submitting, loading = submitting)
            SecondaryButton(text = stringResource(Res.string.common_cancel), onClick = onDismiss, tone = ButtonTone.Cancel, enabled = !submitting)
        },
    )
}

/** Satu baris nota: nama dan harga selalu ada; memilih bahan menambah jumlah dengan satuan bahan itu. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun EntryFields(
    entry: EntryDraft,
    ingredients: ChoicePages<IngredientOption>,
    onRemove: (() -> Unit)?,
    enabled: Boolean,
) {
    val spacing = AppTheme.spacing
    val picked = entry.ingredient
    // Bahan terpilih dan saran bisa berada di luar daftar yang dimuat, jadi ikut dimasukkan.
    val choices = (listOfNotNull(picked) + entry.suggestions + ingredients.items).distinctBy { it.id }

    AppTextField(value = entry.name, onValueChange = { entry.name = it }, label = stringResource(Res.string.expense_name))
    DropdownField(
        label = stringResource(Res.string.expense_ingredient),
        options = listOf(DropdownOption(null, stringResource(Res.string.expense_not_ingredient))) + choices.map { DropdownOption(it.id, it.name) },
        selectedKey = picked?.id,
        onSelect = { key -> entry.pick(choices.firstOrNull { it.id == key }) },
        searchLabel = stringResource(Res.string.expense_search_ingredient),
        emptyText = stringResource(Res.string.expense_no_ingredient),
        onQueryChange = ingredients::search,
        onReachEnd = ingredients::more,
        searching = ingredients.searching,
        loadingMore = ingredients.loadingMore,
    )
    ingredients.failure?.let { InlineMessage(text = failureText(it)) }
    if (picked == null && entry.suggestions.isNotEmpty()) {
        AppText(text = stringResource(Res.string.expense_maybe_ingredient), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
            entry.suggestions.forEach { suggestion ->
                AppChip(label = suggestion.name, selected = false, onClick = { entry.pick(suggestion) })
            }
        }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalAlignment = Alignment.CenterVertically) {
        if (picked != null) {
            val unit = picked.unitName
            AppTextField(
                value = entry.quantity,
                onValueChange = { if (isQuantityTyping(it)) entry.quantity = it },
                label = stringResource(Res.string.expense_quantity),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                trailing = if (unit != null) ({ AppText(text = unit, role = TextRole.Caption, color = AppTheme.colors.contentMuted) }) else null,
                modifier = Modifier.weight(1f),
            )
        }
        MoneyField(
            amount = entry.value,
            onAmountChange = { entry.amount = it?.toString().orEmpty() },
            label = stringResource(Res.string.expense_amount),
            modifier = Modifier.weight(1f),
        )
    }
    if (onRemove != null) {
        SecondaryButton(
            text = stringResource(Res.string.expense_remove_row),
            onClick = onRemove,
            tone = ButtonTone.Danger,
            enabled = enabled,
        )
    }
}

/** Pembeli dipilih dari karyawan aktif semua cabang; kosong berarti yang mencatat, dan nama lama yang diketik bebas tetap bisa dipertahankan. */
@Composable
private fun BuyerField(buyer: String, buyers: ChoicePages<BuyerOption>, onChange: (String) -> Unit) {
    val known = buyers.items.map { option ->
        DropdownOption(option.name, option.outletName?.let { stringResource(Res.string.expense_buyer_of, option.name, it) } ?: option.name)
    }
    val kept = listOfNotNull(DropdownOption(buyer, buyer).takeIf { buyer.isNotBlank() && known.none { it.key == buyer } })
    DropdownField(
        label = stringResource(Res.string.expense_buyer),
        options = listOf(DropdownOption(null, stringResource(Res.string.expense_buyer_self))) + kept + known.distinctBy { it.key },
        selectedKey = buyer.ifBlank { null },
        onSelect = { onChange(it.orEmpty()) },
        searchLabel = stringResource(Res.string.expense_search_buyer),
        emptyText = stringResource(Res.string.expense_no_buyer),
        onQueryChange = buyers::search,
        onReachEnd = buyers::more,
        searching = buyers.searching,
        loadingMore = buyers.loadingMore,
    )
    buyers.failure?.let { InlineMessage(text = failureText(it)) }
}
