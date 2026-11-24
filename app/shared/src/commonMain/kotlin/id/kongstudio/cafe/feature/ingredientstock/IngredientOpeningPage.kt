package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.common_delete
import id.kongstudio.cafe.resources.common_edit
import id.kongstudio.cafe.resources.ingredient_history
import id.kongstudio.cafe.resources.ingredient_stock_now
import id.kongstudio.cafe.resources.movement_count_locked
import id.kongstudio.cafe.resources.movement_delete_message
import id.kongstudio.cafe.resources.movement_delete_title
import id.kongstudio.cafe.resources.movement_edit_title
import id.kongstudio.cafe.resources.movement_kind_adjustment
import id.kongstudio.cafe.resources.movement_kind_in
import id.kongstudio.cafe.resources.movement_kind_sale
import id.kongstudio.cafe.resources.movement_kind_trial
import id.kongstudio.cafe.resources.movement_kind_waste
import id.kongstudio.cafe.resources.movement_opening_locked
import id.kongstudio.cafe.resources.movement_sale_locked
import id.kongstudio.cafe.resources.movement_user
import id.kongstudio.cafe.resources.movement_time
import id.kongstudio.cafe.resources.nav_ingredient_counts
import id.kongstudio.cafe.resources.stock_field_note
import id.kongstudio.cafe.resources.stock_field_qty
import id.kongstudio.cafe.resources.stock_journey_opening
import id.kongstudio.cafe.resources.stock_movement_by
import id.kongstudio.cafe.resources.stock_movements_empty
import id.kongstudio.cafe.resources.stock_opening
import id.kongstudio.cafe.resources.stock_opening_add
import id.kongstudio.cafe.resources.stock_opening_delete
import id.kongstudio.cafe.resources.stock_opening_delete_confirm
import id.kongstudio.cafe.resources.stock_opening_delete_message
import id.kongstudio.cafe.resources.stock_opening_delete_title
import id.kongstudio.cafe.resources.stock_opening_edit
import id.kongstudio.cafe.resources.stock_opening_guard
import id.kongstudio.cafe.resources.stock_opening_period
import id.kongstudio.cafe.resources.stock_opening_problem
import id.kongstudio.cafe.resources.stock_opening_rule
import id.kongstudio.cafe.resources.stock_opening_unset
import id.kongstudio.cafe.resources.stock_problem_qty
import id.kongstudio.cafe.resources.stock_save
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.movementdetailsheet.MovementDetailSheet
import id.kongstudio.cafe.ui.component.pagedlistcard.PagedListCard
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.component.subpage.SubPage
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.feature.userchoice.UserChoiceRepository
import id.kongstudio.cafe.feature.userchoice.userFilter
import id.kongstudio.cafe.resources.filter_picked_tag
import id.kongstudio.cafe.resources.filter_recorded_by
import id.kongstudio.cafe.ui.component.filterbar.FilterBar
import id.kongstudio.cafe.ui.component.filterbar.FilterTag
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.signedquantity.SignedQuantityText
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import id.kongstudio.cafe.resources.stock_now
import id.kongstudio.cafe.resources.stock_confirm_change
import id.kongstudio.cafe.resources.stock_confirm_opening
import id.kongstudio.cafe.resources.stock_correct_before
import org.jetbrains.compose.resources.stringResource

private const val JourneySkeletonRows = 3

/** Hak yang membuka aksi di detail bahan Stok Opname; diputuskan pemanggil dari izin peran, server tetap menolak yang tidak berhak. */
internal class OpeningAccess(val canEditOpening: Boolean, val canCorrect: Boolean)

/** Detail satu bahan di Stok Opname: kartu stok awal dengan aksinya, perjalanan stok periode berjalan, lalu riwayat mutasi berhalaman. */
@Composable
internal fun IngredientOpeningPage(
    ingredient: StockIngredient,
    journey: IngredientJourneyViewModel,
    history: PagedListViewModel<StockMovement>,
    repository: IngredientStockRepository,
    userChoices: UserChoiceRepository,
    access: OpeningAccess,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val journeyState by journey.state.collectAsState()
    val historyState by history.state.collectAsState()
    val recorder = userFilter(history, stringResource(Res.string.filter_recorded_by), userChoices)
    var filling by remember { mutableStateOf(false) }
    var removing by remember { mutableStateOf(false) }
    var viewing by remember { mutableStateOf<StockMovement?>(null) }
    var editing by remember { mutableStateOf<StockMovement?>(null) }
    var deleting by remember { mutableStateOf<StockMovement?>(null) }
    val unit = ingredient.unit

    SubPage(
        title = ingredient.name,
        backLabel = stringResource(Res.string.back_to_page, stringResource(Res.string.nav_ingredient_counts)),
        onBack = onBack,
        modifier = modifier,
        canLeave = !journeyState.saving && !historyState.acting,
    ) {
        journeyState.failure?.let { InlineMessage(text = failureText(it)) }
        val current = journeyState.journey
        if (current == null) {
            if (journeyState.loading) SkeletonRows(count = JourneySkeletonRows)
        } else {
            AppText(text = stringResource(Res.string.stock_opening_period, longDateLabel(current.start)), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            OpeningCard(
                journey = current,
                unit = unit,
                canEdit = access.canEditOpening,
                onFill = {
                    journey.clearSaveFailure()
                    filling = true
                },
                onRemove = {
                    journey.clearSaveFailure()
                    removing = true
                },
            )
            JourneyCard(journey = current, unit = unit)
        }

        val chosen = recorder.selectedLabel
        FilterBar(
            leadingTitle = stringResource(Res.string.ingredient_history),
            searchLabel = null,
            query = "",
            onQueryChange = {},
            showButton = true,
            tags = listOfNotNull(chosen?.let { FilterTag(stringResource(Res.string.filter_picked_tag, recorder.label, it), recorder.onClear) }),
            onClearAll = recorder.onClear,
        ) {
            PickerField(label = recorder.label, valueText = chosen ?: recorder.allLabel, icon = AppIcons.User, onClick = recorder.onOpen)
        }
        historyState.failure?.let { InlineMessage(text = failureText(it)) }
        PagedListCard(
            items = historyState.items,
            page = historyState.page,
            pageCount = history.pageCount,
            onPageChange = history::setPage,
            emptyText = stringResource(Res.string.stock_movements_empty),
            loading = historyState.loading,
        ) { movement ->
            MovementRow(movement = movement, onOpen = {
                history.clearActionFailure()
                viewing = movement
            })
        }
    }

    val current = journeyState.journey
    if (filling && current != null) {
        OpeningForm(
            journey = current,
            unit = unit,
            submitting = journeyState.saving,
            error = journeyState.saveFailure?.let { failureText(it) },
            onSubmit = { qty -> journey.setOpening(qty) { filling = false } },
            onDismiss = {
                journey.clearSaveFailure()
                filling = false
            },
        )
    }

    if (removing && current != null) {
        ConfirmSheet(
            title = stringResource(Res.string.stock_opening_delete_title, ingredient.name),
            message = stringResource(Res.string.stock_opening_delete_message, ingredient.name, StockQuantity.withUnit(current.opening, unit)),
            confirmLabel = stringResource(Res.string.stock_opening_delete_confirm),
            destructive = true,
            enabled = !journeyState.saving,
            onConfirm = { journey.removeOpening { removing = false } },
            onDismiss = {
                journey.clearSaveFailure()
                removing = false
            },
            notice = { journeyState.saveFailure?.let { InlineMessage(text = failureText(it)) } },
        )
    }

    viewing?.let { movement ->
        MovementDetailSheet(
            title = movementKindLabel(movement)?.let { stringResource(it) } ?: ingredient.name,
            quantity = StockQuantity.signed(movement.qty, movement.unit),
            cause = movement.causeLabel,
            note = movement.note,
            userName = movement.userName,
            createdAt = movement.createdAt,
            onDismiss = { viewing = null },
            actions = {
                val locked = when {
                    movement.fromSale -> Res.string.movement_sale_locked
                    movement.fromCount -> Res.string.movement_count_locked
                    movement.fromOpening -> Res.string.movement_opening_locked
                    else -> null
                }
                if (locked != null) {
                    AppText(text = stringResource(locked), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                } else if (access.canCorrect) {
                    historyState.actionFailure?.let { InlineMessage(text = failureText(it)) }
                    // Aksi modal sebaris: batal-arah (Hapus) di kiri, aksi utama (Ubah) di kanan.
                    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
                        SecondaryButton(
                            text = stringResource(Res.string.common_delete),
                            onClick = { deleting = movement },
                            tone = ButtonTone.Danger,
                            modifier = Modifier.weight(1f),
                        )
                        PrimaryButton(
                            text = stringResource(Res.string.common_edit),
                            onClick = {
                                history.clearActionFailure()
                                editing = movement
                            },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            },
        )
    }

    editing?.let { movement ->
        CorrectForm(
            movement = movement,
            submitting = historyState.acting,
            error = historyState.actionFailure?.let { failureText(it) },
            onSubmit = { qty, note ->
                history.act(onSuccess = {
                    editing = null
                    viewing = null
                    journey.reload()
                }) { repository.correct(movement.id, qty, note) }
            },
            onDismiss = {
                history.clearActionFailure()
                editing = null
            },
        )
    }

    deleting?.let { movement ->
        ConfirmSheet(
            title = stringResource(Res.string.movement_delete_title),
            message = stringResource(Res.string.movement_delete_message, StockQuantity.signed(movement.qty, movement.unit)),
            confirmLabel = stringResource(Res.string.common_delete),
            destructive = true,
            enabled = !historyState.acting,
            onConfirm = {
                history.act(onSuccess = {
                    deleting = null
                    viewing = null
                    journey.reload()
                }) { repository.remove(movement.id) }
            },
            onDismiss = {
                history.clearActionFailure()
                deleting = null
            },
            notice = { historyState.actionFailure?.let { InlineMessage(text = failureText(it)) } },
        )
    }
}

@Composable
private fun OpeningCard(journey: StockJourney, unit: String?, canEdit: Boolean, onFill: () -> Unit, onRemove: () -> Unit) {
    if (!journey.openingSet) {
        DetailCard(rows = listOf(stringResource(Res.string.stock_opening) to stringResource(Res.string.stock_opening_unset)))
        if (canEdit) PrimaryButton(text = stringResource(Res.string.stock_opening_add), onClick = onFill)
        return
    }
    DetailCard(
        rows = listOf(
            stringResource(Res.string.stock_opening) to StockQuantity.withUnit(journey.opening, unit),
            stringResource(Res.string.movement_user) to journey.openingBy,
            stringResource(Res.string.movement_time) to stampLabel(journey.openingAt),
        ),
    )
    // Susunan sama dengan lembar rincian mutasi: Hapus di kiri, Ubah sebagai aksi utama di kanan.
    if (canEdit) {
        Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            SecondaryButton(text = stringResource(Res.string.stock_opening_delete), onClick = onRemove, tone = ButtonTone.Danger, modifier = Modifier.weight(1f))
            PrimaryButton(text = stringResource(Res.string.stock_opening_edit), onClick = onFill, modifier = Modifier.weight(1f))
        }
    }
}

@Composable
private fun JourneyCard(journey: StockJourney, unit: String?) {
    DetailCard(
        rows = listOf(
            // Stok awal yang belum diisi sudah disebut di kartu Stok awal di atasnya; di sini dihitung nol supaya jumlahnya tetap terbaca.
            stringResource(Res.string.stock_journey_opening) to StockQuantity.withUnit(if (journey.openingSet) journey.opening else "0", unit),
            stringResource(Res.string.movement_kind_in) to StockQuantity.signed(journey.received, unit),
            stringResource(Res.string.movement_kind_sale) to StockQuantity.signed(journey.sold, unit),
            stringResource(Res.string.movement_kind_waste) to StockQuantity.signed(journey.wasted, unit),
            stringResource(Res.string.movement_kind_trial) to StockQuantity.signed(journey.trial, unit),
            stringResource(Res.string.movement_kind_adjustment) to StockQuantity.signed(journey.adjusted, unit),
            stringResource(Res.string.ingredient_stock_now) to StockQuantity.withUnit(journey.stock, unit),
        ),
    )
}

/** Jenis di judul, catatan, orang dan waktu, dengan jumlah bertanda di kanan: kurang berwarna bahaya, tambah berwarna utama. */
@Composable
private fun MovementRow(movement: StockMovement, onOpen: () -> Unit) {
    ListRow(
        title = movementKindLabel(movement)?.let { stringResource(it) } ?: movement.ingredientName,
        caption = listOfNotNull(movement.causeLabel, movement.note).joinToString(" · ").ifEmpty { null },
        footnote = stringResource(Res.string.stock_movement_by, movement.userName.orEmpty(), stampLabel(movement.createdAt)).trim(' ', '·'),
        trailing = { SignedQuantityText(qty = movement.qty, unit = movement.unit) },
        opensDetail = true,
        onClick = onOpen,
    )
}

@Composable
private fun OpeningForm(
    journey: StockJourney,
    unit: String?,
    submitting: Boolean,
    error: String?,
    onSubmit: (qty: String) -> Unit,
    onDismiss: () -> Unit,
) {
    var text by remember { mutableStateOf(if (journey.openingSet) StockQuantity.show(journey.opening) else "") }
    var invalid by remember { mutableStateOf(false) }
    var confirming by remember { mutableStateOf<String?>(null) }
    val received = (journey.received.toDoubleOrNull() ?: 0.0) > 0.0

    FormSheet(
        title = stringResource(if (journey.openingSet) Res.string.stock_opening_edit else Res.string.stock_opening_add),
        submitLabel = stringResource(Res.string.stock_save),
        onSubmit = {
            val qty = StockQuantity.parse(text)
            invalid = qty == null
            if (qty != null) confirming = qty
        },
        onDismiss = onDismiss,
        submitting = submitting,
        loadingOnSubmit = true,
        error = if (invalid) stringResource(Res.string.stock_opening_problem) else error,
    ) {
        AppText(text = stringResource(Res.string.stock_opening_rule), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        if (received) {
            StatusBanner(text = stringResource(Res.string.stock_opening_guard, StockQuantity.withUnit(journey.received, unit)), tone = BannerTone.Warning)
        }
        AppText(text = stringResource(Res.string.stock_now, StockQuantity.withUnit(journey.stock, unit)), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        QuantityField(
            value = text,
            onValueChange = {
                text = it
                invalid = false
            },
            label = stringResource(Res.string.stock_opening),
            unit = unit,
            isError = invalid,
        )
    }

    // Stok awal mengubah seluruh perhitungan periode, jadi nilai lama dan baru diperlihatkan dulu.
    confirming?.let { qty ->
        val next = StockQuantity.withUnit(qty, unit)
        ConfirmSheet(
            title = stringResource(if (journey.openingSet) Res.string.stock_opening_edit else Res.string.stock_opening_add),
            message = if (journey.openingSet) {
                stringResource(Res.string.stock_confirm_change, StockQuantity.withUnit(journey.opening, unit), next)
            } else {
                stringResource(Res.string.stock_confirm_opening, next)
            },
            confirmLabel = stringResource(Res.string.stock_save),
            enabled = !submitting,
            onConfirm = {
                confirming = null
                onSubmit(qty)
            },
            onDismiss = { confirming = null },
        )
    }
}

@Composable
internal fun CorrectForm(
    movement: StockMovement,
    submitting: Boolean,
    error: String?,
    onSubmit: (qty: String, note: String) -> Unit,
    onDismiss: () -> Unit,
) {
    var qtyText by remember { mutableStateOf(StockQuantity.show(movement.qty.removePrefix("-"))) }
    var note by remember { mutableStateOf(movement.note.orEmpty()) }
    var invalid by remember { mutableStateOf(false) }
    var confirming by remember { mutableStateOf<String?>(null) }
    // Arah catatan tidak pernah berubah saat dikoreksi, jadi tanda jumlah baru mengikuti tanda lama.
    val negative = StockQuantity.isNegative(movement.qty)

    FormSheet(
        title = stringResource(Res.string.movement_edit_title),
        submitLabel = stringResource(Res.string.stock_save),
        onSubmit = {
            val qty = StockQuantity.parsePositive(qtyText)
            invalid = qty == null
            if (qty != null) confirming = qty
        },
        onDismiss = onDismiss,
        submitting = submitting,
        error = if (invalid) stringResource(Res.string.stock_problem_qty) else error,
    ) {
        AppText(
            text = stringResource(Res.string.stock_correct_before, StockQuantity.signed(movement.qty, movement.unit)),
            role = TextRole.Caption,
            color = AppTheme.colors.contentMuted,
        )
        QuantityField(
            value = qtyText,
            onValueChange = {
                qtyText = it
                invalid = false
            },
            label = stringResource(Res.string.stock_field_qty),
            unit = movement.unit,
            isError = invalid,
        )
        AppTextField(value = note, onValueChange = { note = it }, label = stringResource(Res.string.stock_field_note))
    }

    confirming?.let { qty ->
        ConfirmSheet(
            title = stringResource(Res.string.movement_edit_title),
            message = stringResource(
                Res.string.stock_confirm_change,
                StockQuantity.signed(movement.qty, movement.unit),
                StockQuantity.signed(if (negative) "-$qty" else qty, movement.unit),
            ),
            confirmLabel = stringResource(Res.string.stock_save),
            enabled = !submitting,
            onConfirm = {
                confirming = null
                onSubmit(qty, note)
            },
            onDismiss = { confirming = null },
        )
    }
}
