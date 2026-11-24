package id.kongstudio.cafe.feature.ingredientstock

import id.kongstudio.cafe.feature.periods.BranchPeriodsViewModel
import id.kongstudio.cafe.feature.periods.periodDateRange
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.common_all
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_edit
import id.kongstudio.cafe.resources.common_note
import id.kongstudio.cafe.resources.filter_recorded_by
import id.kongstudio.cafe.resources.movement_cause
import id.kongstudio.cafe.resources.movement_count_locked
import id.kongstudio.cafe.resources.movement_delete_message
import id.kongstudio.cafe.resources.movement_delete_title
import id.kongstudio.cafe.resources.movement_kind
import id.kongstudio.cafe.resources.movement_kind_trial
import id.kongstudio.cafe.resources.movement_kind_waste
import id.kongstudio.cafe.resources.movement_opening_locked
import id.kongstudio.cafe.resources.movement_quantity
import id.kongstudio.cafe.resources.movement_sale_locked
import id.kongstudio.cafe.resources.movement_user
import id.kongstudio.cafe.resources.movement_time
import id.kongstudio.cafe.resources.nav_ingredient_receipts
import id.kongstudio.cafe.resources.nav_ingredient_waste
import id.kongstudio.cafe.resources.stock_field_cause
import id.kongstudio.cafe.resources.stock_field_ingredient
import id.kongstudio.cafe.resources.stock_field_note
import id.kongstudio.cafe.resources.stock_field_note_required
import id.kongstudio.cafe.resources.stock_field_qty
import id.kongstudio.cafe.resources.stock_form_receipt
import id.kongstudio.cafe.resources.stock_form_trial
import id.kongstudio.cafe.resources.stock_form_waste
import id.kongstudio.cafe.resources.stock_movement_by
import id.kongstudio.cafe.resources.stock_movement_search
import id.kongstudio.cafe.resources.stock_movements_empty
import id.kongstudio.cafe.resources.stock_pick_cause
import id.kongstudio.cafe.resources.stock_pick_ingredient
import id.kongstudio.cafe.resources.stock_problem_cause
import id.kongstudio.cafe.resources.stock_problem_ingredient
import id.kongstudio.cafe.resources.stock_problem_kind
import id.kongstudio.cafe.resources.stock_problem_note
import id.kongstudio.cafe.resources.stock_problem_qty
import id.kongstudio.cafe.resources.stock_receipt_add
import id.kongstudio.cafe.resources.stock_save
import id.kongstudio.cafe.resources.stock_waste_add
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownField
import id.kongstudio.cafe.ui.component.dropdownfield.DropdownOption
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.ui.component.resourcelist.ResourceFilter
import id.kongstudio.cafe.ui.component.resourcelist.ResourceList
import id.kongstudio.cafe.ui.component.resourcelist.nameSortOptions
import id.kongstudio.cafe.ui.component.resourcelist.sortLabel
import id.kongstudio.cafe.ui.component.resourcelist.timeSortOptions
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.subpage.SubPage
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.signedquantity.SignedQuantityText
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.photofield.PhotoField
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.resources.stock_proof_missed
import id.kongstudio.cafe.resources.stock_proof_none
import id.kongstudio.cafe.resources.stock_proof_receipt
import id.kongstudio.cafe.resources.stock_proof_waste
import id.kongstudio.cafe.resources.stock_proof_optional
import id.kongstudio.cafe.resources.stock_now
import id.kongstudio.cafe.resources.stock_field_count_by
import id.kongstudio.cafe.resources.stock_count_by_package
import id.kongstudio.cafe.resources.stock_count_by_unit
import id.kongstudio.cafe.resources.stock_field_packages
import id.kongstudio.cafe.resources.stock_unit_package
import id.kongstudio.cafe.resources.stock_package_large
import id.kongstudio.cafe.resources.stock_package_result
import id.kongstudio.cafe.resources.stock_confirm_title
import id.kongstudio.cafe.resources.stock_confirm_line
import id.kongstudio.cafe.resources.stock_confirm_packages
import id.kongstudio.cafe.resources.stock_confirm_with_photo
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import org.jetbrains.compose.resources.stringResource

/** Dua layar pencatatan: barang masuk, serta rusak dan RnD yang berbagi satu daftar dengan penyaring Jenis. */
internal enum class EntryMode { Receipts, WasteAndTrial }

private enum class EntryProblem { Kind, Ingredient, Quantity, Cause, Note }

/** Penyaring Jenis kosong berarti Rusak dan RnD sekaligus. */
internal fun movementKindsOf(mode: EntryMode, filter: String): Set<MovementKind> = when {
    mode == EntryMode.Receipts -> setOf(MovementKind.Receipt)
    filter == MovementKind.Waste.code -> setOf(MovementKind.Waste)
    filter == MovementKind.Trial.code -> setOf(MovementKind.Trial)
    else -> setOf(MovementKind.Waste, MovementKind.Trial)
}

/** Batas hitungan kemasan yang masih lazim sekali masuk; di atasnya kasir diminta memeriksa satuannya. */
private const val LargePackageCount = 100

@Composable
internal fun IngredientEntryScreen(
    mode: EntryMode,
    viewModel: PagedListViewModel<StockMovement>,
    repository: IngredientStockRepository,
    userChoices: UserChoiceRepository,
    access: UserAccess,
    periods: BranchPeriodsViewModel,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val today = BusinessDay.today()
    val recorder = userFilter(viewModel, stringResource(Res.string.filter_recorded_by), userChoices)
    var adding by remember { mutableStateOf(false) }
    var viewingId by remember { mutableStateOf<String?>(null) }
    var proofMissed by remember { mutableStateOf(false) }
    // Tombol tambah hanya untuk yang berhak menulis; yang hanya boleh membaca melihat riwayatnya saja.
    val canWrite = if (mode == EntryMode.Receipts) access.allows(Permission.StockReceive) else access.allows(Permission.StockAdjust)
    val actionError = state.actionFailure?.let { failureText(it) }
    val title = stringResource(if (mode == EntryMode.Receipts) Res.string.nav_ingredient_receipts else Res.string.nav_ingredient_waste)
    val viewing = viewingId?.let { id -> state.items.firstOrNull { it.id == id } }

    if (viewing != null) {
        MovementPage(
            movement = viewing,
            listTitle = title,
            viewModel = viewModel,
            repository = repository,
            canCorrect = access.allows(Permission.StockCorrect),
            canAttach = canWrite,
            proofMissed = proofMissed,
            onBack = {
                viewingId = null
                proofMissed = false
            },
            modifier = modifier,
        )
        return
    }

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
        emptyText = stringResource(Res.string.stock_movements_empty),
        modifier = modifier,
        searchLabel = stringResource(Res.string.stock_movement_search),
        query = state.query,
        onQueryChange = viewModel::setQuery,
        filters = if (mode == EntryMode.WasteAndTrial) {
            listOf(
                ResourceFilter("", stringResource(Res.string.common_all)),
                ResourceFilter(MovementKind.Waste.code, stringResource(Res.string.movement_kind_waste)),
                ResourceFilter(MovementKind.Trial.code, stringResource(Res.string.movement_kind_trial)),
            )
        } else {
            emptyList()
        },
        filterLabel = stringResource(Res.string.movement_kind),
        selectedFilter = state.filter,
        onFilterChange = viewModel::setFilter,
        pickers = listOf(recorder),
        dateRange = periodDateRange(viewModel, periods, today),
        sortLabel = sortLabel(),
        sortOptions = timeSortOptions() + nameSortOptions(),
        selectedSort = state.sort,
        onSortChange = viewModel::setSort,
        addLabel = if (canWrite) stringResource(if (mode == EntryMode.Receipts) Res.string.stock_receipt_add else Res.string.stock_waste_add) else null,
        onAdd = if (canWrite) {
            {
                viewModel.clearActionFailure()
                adding = true
            }
        } else {
            null
        },
        actionError = actionError.takeIf { !adding },
    ) { movement ->
        // Jenis hanya disebut saat Rusak dan RnD tampil bersama, supaya baris tidak mengulang penyaring yang sedang dipakai.
        val kindLabel = movementKindLabel(movement)?.takeIf { mode == EntryMode.WasteAndTrial && state.filter.isEmpty() }?.let { stringResource(it) }
        ListRow(
            title = movement.ingredientName,
            caption = listOfNotNull(kindLabel, movement.causeLabel, movement.note).joinToString(" · ").ifEmpty { null },
            footnote = stringResource(Res.string.stock_movement_by, movement.userName.orEmpty(), stampLabel(movement.createdAt)).trim(' ', '·'),
            trailing = { SignedQuantityText(qty = movement.qty, unit = movement.unit) },
            opensDetail = true,
            onClick = {
                viewModel.clearActionFailure()
                viewingId = movement.id
            },
        )
    }

    if (adding) {
        EntryForm(
            mode = mode,
            initialKind = movementKindsOf(mode, state.filter).singleOrNull(),
            repository = repository,
            submitting = state.acting,
            error = actionError,
            onSubmit = { entry ->
                var saved: EntrySaved? = null
                viewModel.act(onSuccess = {
                    adding = false
                    // Foto yang gagal terunggah tidak membatalkan catatan; rinciannya dibuka supaya foto bisa dilampirkan ulang.
                    saved?.takeIf { !it.proofSaved }?.let {
                        viewingId = it.id
                        proofMissed = true
                    }
                }) {
                    when (entry.kind) {
                        MovementKind.Receipt -> repository.receive(entry.ingredient.id, entry.qty, entry.note, entry.proof)
                        MovementKind.Waste -> repository.waste(entry.ingredient.id, entry.qty, entry.cause, entry.note, entry.proof)
                        MovementKind.Trial -> repository.trial(entry.ingredient.id, entry.qty, entry.note)
                    }.also { result -> if (result is DeviceResult.Ok) saved = result.value }
                }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                adding = false
            },
        )
    }
}

/** Halaman rincian satu catatan, dibuka dari barisnya; ubah dan hapus ada di sini bagi yang berhak mengoreksi. */
@Composable
private fun MovementPage(
    movement: StockMovement,
    listTitle: String,
    viewModel: PagedListViewModel<StockMovement>,
    repository: IngredientStockRepository,
    canCorrect: Boolean,
    canAttach: Boolean,
    proofMissed: Boolean,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    var editing by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf(false) }
    var attached by remember(movement.id) { mutableStateOf(false) }
    val failure = state.actionFailure?.let { failureText(it) }
    // Foto hanya untuk catatan yang dibuat tangan: barang masuk dan rusak, bukan penjualan, penutupan, atau stok awal.
    val takesProof = movement.editable && (movement.kind == CardKind.In || movement.kind == CardKind.Waste)

    SubPage(
        title = movement.ingredientName,
        backLabel = stringResource(Res.string.back_to_page, listTitle),
        onBack = onBack,
        modifier = modifier,
        canLeave = !state.acting,
    ) {
        DetailCard(
            rows = listOf(
                stringResource(Res.string.movement_kind) to movementKindLabel(movement)?.let { stringResource(it) },
                stringResource(Res.string.movement_quantity) to StockQuantity.signed(movement.qty, movement.unit),
                stringResource(Res.string.movement_cause) to movement.causeLabel,
                stringResource(Res.string.common_note) to movement.note,
                stringResource(Res.string.movement_user) to movement.userName,
                stringResource(Res.string.movement_time) to stampLabel(movement.createdAt),
            ),
        )
        if (proofMissed && movement.proofUrl == null && !attached) {
            InlineMessage(text = stringResource(Res.string.stock_proof_missed))
        }
        if (takesProof) {
            SectionTitle(stringResource(proofTitleOf(movement.kind)))
            movement.proofUrl?.let { RemoteImage(url = it, contentDescription = stringResource(proofTitleOf(movement.kind)), fit = true) }
            if (movement.proofUrl == null && !canAttach) {
                AppText(text = stringResource(Res.string.stock_proof_none), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            }
            if (canAttach) {
                PhotoField(
                    photo = null,
                    onPicked = { photo ->
                        viewModel.act(onSuccess = { attached = true }) { repository.attachProof(movement.id, photo.bytes) }
                    },
                    enabled = !state.acting,
                )
            }
        }
        val locked = when {
            movement.fromSale -> Res.string.movement_sale_locked
            movement.fromCount -> Res.string.movement_count_locked
            movement.fromOpening -> Res.string.movement_opening_locked
            else -> null
        }
        if (locked != null) {
            AppText(text = stringResource(locked), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        } else if (canCorrect) {
            if (!editing && !deleting) failure?.let { InlineMessage(text = it) }
            // Susunan sama dengan rincian riwayat Stok Opname: Hapus di kiri, Ubah sebagai aksi utama di kanan.
            Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
                SecondaryButton(
                    text = stringResource(Res.string.common_delete),
                    onClick = {
                        viewModel.clearActionFailure()
                        deleting = true
                    },
                    tone = ButtonTone.Danger,
                    modifier = Modifier.weight(1f),
                )
                PrimaryButton(
                    text = stringResource(Res.string.common_edit),
                    onClick = {
                        viewModel.clearActionFailure()
                        editing = true
                    },
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }

    if (editing) {
        CorrectForm(
            movement = movement,
            submitting = state.acting,
            error = failure,
            onSubmit = { qty, note -> viewModel.act(onSuccess = { editing = false }) { repository.correct(movement.id, qty, note) } },
            onDismiss = {
                viewModel.clearActionFailure()
                editing = false
            },
        )
    }

    if (deleting) {
        ConfirmSheet(
            title = stringResource(Res.string.movement_delete_title),
            message = stringResource(Res.string.movement_delete_message, StockQuantity.signed(movement.qty, movement.unit)),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !state.acting,
            onConfirm = {
                viewModel.act(onSuccess = {
                    deleting = false
                    onBack()
                }) { repository.remove(movement.id) }
            },
            onDismiss = {
                viewModel.clearActionFailure()
                deleting = false
            },
            notice = { failure?.let { InlineMessage(text = it) } },
        )
    }
}

/** Isian yang sudah sah dan siap disimpan; [qty] selalu dalam satuan bahan, [packages] terisi bila dicatat per kemasan. */
private class EntryInput(
    val kind: MovementKind,
    val ingredient: StockIngredient,
    val qty: String,
    val packages: String?,
    val cause: String,
    val causeLabel: String?,
    val note: String,
    val proof: ByteArray?,
)

private fun proofTitleOf(kind: CardKind) = if (kind == CardKind.In) Res.string.stock_proof_receipt else Res.string.stock_proof_waste

@Composable
private fun EntryForm(
    mode: EntryMode,
    initialKind: MovementKind?,
    repository: IngredientStockRepository,
    submitting: Boolean,
    error: String?,
    onSubmit: (EntryInput) -> Unit,
    onDismiss: () -> Unit,
) {
    val choices = listOf(MovementKind.Waste, MovementKind.Trial)
    var kind by remember { mutableStateOf(if (mode == EntryMode.Receipts) MovementKind.Receipt else initialKind) }
    var picked by remember { mutableStateOf<StockIngredient?>(null) }
    var picking by remember { mutableStateOf(false) }
    var qtyText by remember { mutableStateOf("") }
    var byPackage by remember { mutableStateOf(false) }
    var note by remember { mutableStateOf("") }
    var causes by remember { mutableStateOf<List<WasteCause>>(emptyList()) }
    var causesFailure by remember { mutableStateOf<AppFailure?>(null) }
    var cause by remember { mutableStateOf<String?>(null) }
    var photo by remember { mutableStateOf<PickedPhoto?>(null) }
    var problem by remember { mutableStateOf<EntryProblem?>(null) }
    var confirming by remember { mutableStateOf<EntryInput?>(null) }

    LaunchedEffect(mode) {
        if (mode == EntryMode.WasteAndTrial) {
            when (val result = repository.causes()) {
                is DeviceResult.Ok -> {
                    causes = result.value
                    causesFailure = null
                }
                is DeviceResult.Failed -> causesFailure = result.failure
            }
        }
    }

    // Jumlah dalam satuan bahan: per kemasan dikali isi kemasan, selain itu apa adanya; dihitung dari isian terkini.
    fun quantityOf(chosen: StockIngredient?, text: String, perPackage: Boolean): String? {
        val typed = StockQuantity.parsePositive(text) ?: return null
        return if (perPackage && chosen != null) StockQuantity.times(typed, chosen.packageSize) else typed
    }

    val ingredient = picked
    val packaged = ingredient?.packaged == true && byPackage
    val qty = quantityOf(ingredient, qtyText, packaged)

    fun submit() {
        val chosenKind = kind
        val chosen = picked
        val perPackage = chosen?.packaged == true && byPackage
        val typed = StockQuantity.parsePositive(qtyText)
        val qty = quantityOf(chosen, qtyText, perPackage)
        problem = when {
            chosenKind == null -> EntryProblem.Kind
            chosen == null -> EntryProblem.Ingredient
            qty == null -> EntryProblem.Quantity
            chosenKind == MovementKind.Waste && cause == null -> EntryProblem.Cause
            chosenKind == MovementKind.Trial && note.isBlank() -> EntryProblem.Note
            else -> null
        }
        if (problem != null || chosenKind == null || chosen == null || qty == null) return
        confirming = EntryInput(
            kind = chosenKind,
            ingredient = chosen,
            qty = qty,
            packages = typed.takeIf { perPackage },
            cause = if (chosenKind == MovementKind.Waste) cause.orEmpty() else "",
            causeLabel = causes.firstOrNull { it.code == cause }?.label.takeIf { chosenKind == MovementKind.Waste },
            note = note,
            proof = photo?.bytes.takeIf { chosenKind != MovementKind.Trial },
        )
    }

    val title = stringResource(
        when (kind) {
            MovementKind.Receipt -> Res.string.stock_form_receipt
            MovementKind.Trial -> Res.string.stock_form_trial
            MovementKind.Waste -> Res.string.stock_form_waste
            null -> Res.string.stock_waste_add
        },
    )
    val problemText = problem?.let {
        stringResource(
            when (it) {
                EntryProblem.Kind -> Res.string.stock_problem_kind
                EntryProblem.Ingredient -> Res.string.stock_problem_ingredient
                EntryProblem.Quantity -> Res.string.stock_problem_qty
                EntryProblem.Cause -> Res.string.stock_problem_cause
                EntryProblem.Note -> Res.string.stock_problem_note
            },
        )
    }

    FormSheet(
        title = title,
        submitLabel = stringResource(Res.string.stock_save),
        onSubmit = ::submit,
        onDismiss = onDismiss,
        submitting = submitting,
        error = problemText ?: error ?: causesFailure?.let { failureText(it) },
    ) {
        if (mode == EntryMode.WasteAndTrial) {
            ChoiceGroup(
                label = stringResource(Res.string.movement_kind),
                options = listOf(stringResource(Res.string.movement_kind_waste), stringResource(Res.string.movement_kind_trial)),
                selectedIndex = choices.indexOf(kind).takeIf { it >= 0 },
                onSelect = {
                    kind = choices[it]
                    if (problem == EntryProblem.Kind) problem = null
                },
            )
        }
        PickerField(
            label = stringResource(Res.string.stock_field_ingredient),
            valueText = ingredient?.name ?: stringResource(Res.string.stock_pick_ingredient),
            icon = AppIcons.KitchenTools,
            onClick = { picking = true },
        )
        ingredient?.let {
            AppText(
                text = stringResource(Res.string.stock_now, StockQuantity.withUnit(it.stock, it.unit)),
                role = TextRole.Caption,
                color = AppTheme.colors.contentMuted,
            )
        }
        // Kemasan hanya ditawarkan untuk barang masuk, karena yang rusak atau dipakai RnD jarang satu kemasan utuh.
        if (ingredient != null && ingredient.packaged && kind == MovementKind.Receipt) {
            val unit = ingredient.unit.orEmpty()
            ChoiceGroup(
                label = stringResource(Res.string.stock_field_count_by),
                options = listOf(
                    stringResource(Res.string.stock_count_by_package, StockQuantity.withUnit(ingredient.packageSize, ingredient.unit)),
                    stringResource(Res.string.stock_count_by_unit, unit),
                ),
                selectedIndex = if (byPackage) 0 else 1,
                onSelect = {
                    byPackage = it == 0
                    if (problem == EntryProblem.Quantity) problem = null
                },
            )
        }
        QuantityField(
            value = qtyText,
            onValueChange = {
                qtyText = it
                if (problem == EntryProblem.Quantity) problem = null
            },
            label = stringResource(if (packaged) Res.string.stock_field_packages else Res.string.stock_field_qty),
            unit = if (packaged) stringResource(Res.string.stock_unit_package) else ingredient?.unit,
            isError = problem == EntryProblem.Quantity,
        )
        if (packaged && qty != null && ingredient != null) {
            AppText(
                text = stringResource(Res.string.stock_package_result, StockQuantity.withUnit(qty, ingredient.unit)),
                role = TextRole.Label,
                color = AppTheme.colors.primary,
            )
            // Hitungan kemasan yang tidak lazim biasanya salah satuan: yang diketik jumlah satuan dasar, bukan kemasan.
            val typedPackages = StockQuantity.parsePositive(qtyText)?.toDoubleOrNull()
            if (typedPackages != null && typedPackages > LargePackageCount) {
                AppText(
                    text = stringResource(Res.string.stock_package_large, StockQuantity.display(qtyText.trim()), ingredient.unit.orEmpty()),
                    role = TextRole.Caption,
                    color = AppTheme.colors.warning,
                )
            }
        }
        if (kind == MovementKind.Waste && causes.isNotEmpty()) {
            DropdownField(
                label = stringResource(Res.string.stock_field_cause),
                options = listOf(DropdownOption(null, stringResource(Res.string.stock_pick_cause))) + causes.map { DropdownOption(it.code, it.label) },
                selectedKey = cause,
                onSelect = {
                    cause = it
                    if (problem == EntryProblem.Cause) problem = null
                },
            )
        }
        AppTextField(
            value = note,
            onValueChange = {
                note = it
                if (problem == EntryProblem.Note) problem = null
            },
            label = stringResource(if (kind == MovementKind.Trial) Res.string.stock_field_note_required else Res.string.stock_field_note),
            isError = problem == EntryProblem.Note,
        )
        val proofKind = when (kind) {
            MovementKind.Receipt -> CardKind.In
            MovementKind.Waste -> CardKind.Waste
            else -> null
        }
        if (proofKind != null) {
            AppText(text = stringResource(Res.string.stock_proof_optional, stringResource(proofTitleOf(proofKind))), role = TextRole.Label)
            PhotoField(photo = photo, onPicked = { photo = it }, enabled = !submitting)
        }
    }

    if (picking) {
        IngredientPicker(
            repository = repository,
            onPicked = {
                picked = it
                picking = false
                byPackage = it.packaged
                if (problem == EntryProblem.Ingredient) problem = null
            },
            onDismiss = { picking = false },
        )
    }

    confirming?.let { entry ->
        val amount = StockQuantity.withUnit(entry.qty, entry.ingredient.unit)
        val shown = if (entry.kind == MovementKind.Receipt) "+$amount" else "−$amount"
        ConfirmSheet(
            title = stringResource(Res.string.stock_confirm_title, title.replaceFirstChar { it.lowercase() }),
            message = listOfNotNull(
                stringResource(Res.string.stock_confirm_line, shown, entry.ingredient.name),
                entry.packages?.let { stringResource(Res.string.stock_confirm_packages, StockQuantity.display(it), StockQuantity.withUnit(entry.ingredient.packageSize, entry.ingredient.unit)) },
                entry.causeLabel,
                entry.note.trim().ifEmpty { null },
                stringResource(Res.string.stock_confirm_with_photo).takeIf { entry.proof != null },
            ).joinToString("\n"),
            confirmLabel = stringResource(Res.string.stock_save),
            enabled = !submitting,
            onConfirm = {
                confirming = null
                onSubmit(entry)
            },
            onDismiss = { confirming = null },
        )
    }
}
