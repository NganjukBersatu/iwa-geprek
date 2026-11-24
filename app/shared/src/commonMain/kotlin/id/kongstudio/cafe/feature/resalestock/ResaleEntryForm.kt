package id.kongstudio.cafe.feature.resalestock

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.resale_field_kind
import id.kongstudio.cafe.resources.resale_field_reason
import id.kongstudio.cafe.resources.resale_kind_decrease
import id.kongstudio.cafe.resources.resale_kind_increase
import id.kongstudio.cafe.resources.resale_kind_receive
import id.kongstudio.cafe.resources.resale_problem_reason
import id.kongstudio.cafe.resources.stock_confirm_line
import id.kongstudio.cafe.resources.stock_confirm_title
import id.kongstudio.cafe.resources.stock_field_note
import id.kongstudio.cafe.resources.stock_field_qty
import id.kongstudio.cafe.resources.stock_now
import id.kongstudio.cafe.resources.stock_problem_qty
import id.kongstudio.cafe.resources.stock_save
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

internal enum class ResaleAction { Receive, Increase, Decrease }

private enum class EntryProblem { Quantity, Reason }

private const val MinReasonLength = 3

/**
 * Satu formulir untuk tiga catatan: barang masuk, penyesuaian tambah, dan penyesuaian kurang; pilihannya hanya yang diizinkan peran.
 * Susunannya sama dengan Barang Masuk bahan: stok saat ini, satuan menempel di isian, dan konfirmasi sebelum disimpan.
 */
@Composable
internal fun ResaleEntryForm(
    item: ResaleItem,
    actions: List<ResaleAction>,
    submitting: Boolean,
    error: String?,
    onSubmit: (action: ResaleAction, qty: String, note: String) -> Unit,
    onDismiss: () -> Unit,
) {
    var actionIndex by remember { mutableStateOf(0) }
    var qtyText by remember { mutableStateOf("") }
    var note by remember { mutableStateOf("") }
    var problem by remember { mutableStateOf<EntryProblem?>(null) }
    var confirming by remember { mutableStateOf<String?>(null) }
    val action = actions[actionIndex]

    fun submit() {
        val qty = StockQuantity.parsePositive(qtyText)
        problem = when {
            qty == null -> EntryProblem.Quantity
            action != ResaleAction.Receive && note.trim().length < MinReasonLength -> EntryProblem.Reason
            else -> null
        }
        if (problem == null && qty != null) confirming = qty
    }

    val labels = actions.map {
        stringResource(
            when (it) {
                ResaleAction.Receive -> Res.string.resale_kind_receive
                ResaleAction.Increase -> Res.string.resale_kind_increase
                ResaleAction.Decrease -> Res.string.resale_kind_decrease
            },
        )
    }
    val problemText = problem?.let {
        stringResource(if (it == EntryProblem.Quantity) Res.string.stock_problem_qty else Res.string.resale_problem_reason)
    }

    FormSheet(
        title = item.name,
        submitLabel = stringResource(Res.string.stock_save),
        onSubmit = ::submit,
        onDismiss = onDismiss,
        submitting = submitting,
        error = problemText ?: error,
    ) {
        AppText(text = stringResource(Res.string.stock_now, StockQuantity.withUnit(item.stock, item.unit)), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        if (actions.size > 1) {
            ChoiceFlow(
                label = stringResource(Res.string.resale_field_kind),
                options = labels,
                selectedIndex = actionIndex,
                onSelect = {
                    actionIndex = it
                    problem = null
                },
            )
        }
        QuantityField(
            value = qtyText,
            onValueChange = {
                qtyText = it
                if (problem == EntryProblem.Quantity) problem = null
            },
            label = stringResource(Res.string.stock_field_qty),
            unit = item.unit,
            isError = problem == EntryProblem.Quantity,
        )
        AppTextField(
            value = note,
            onValueChange = {
                note = it
                if (problem == EntryProblem.Reason) problem = null
            },
            label = stringResource(if (action == ResaleAction.Receive) Res.string.stock_field_note else Res.string.resale_field_reason),
            isError = problem == EntryProblem.Reason,
        )
    }

    confirming?.let { qty ->
        val amount = StockQuantity.withUnit(qty, item.unit)
        val shown = if (action == ResaleAction.Decrease) "−$amount" else "+$amount"
        ConfirmSheet(
            title = stringResource(Res.string.stock_confirm_title, labels[actionIndex].replaceFirstChar { it.lowercase() }),
            message = listOfNotNull(stringResource(Res.string.stock_confirm_line, shown, item.name), note.trim().ifEmpty { null }).joinToString("\n"),
            confirmLabel = stringResource(Res.string.stock_save),
            enabled = !submitting,
            onConfirm = {
                confirming = null
                onSubmit(action, qty, note)
            },
            onDismiss = { confirming = null },
        )
    }
}
