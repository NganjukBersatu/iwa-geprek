package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.back_to_page
import id.kongstudio.cafe.resources.stock_field_ingredient
import id.kongstudio.cafe.resources.stock_now
import id.kongstudio.cafe.resources.stock_opening
import id.kongstudio.cafe.resources.stock_opening_bulk
import id.kongstudio.cafe.resources.stock_opening_bulk_add_line
import id.kongstudio.cafe.resources.stock_opening_bulk_confirm
import id.kongstudio.cafe.resources.stock_opening_bulk_confirm_title
import id.kongstudio.cafe.resources.stock_opening_bulk_done
import id.kongstudio.cafe.resources.stock_opening_bulk_duplicate
import id.kongstudio.cafe.resources.stock_opening_bulk_failed
import id.kongstudio.cafe.resources.stock_opening_bulk_hint
import id.kongstudio.cafe.resources.stock_opening_bulk_no_ingredient
import id.kongstudio.cafe.resources.stock_opening_bulk_remove_line
import id.kongstudio.cafe.resources.stock_opening_bulk_save
import id.kongstudio.cafe.resources.stock_opening_missing
import id.kongstudio.cafe.resources.stock_opening_problem
import id.kongstudio.cafe.resources.stock_opening_rule
import id.kongstudio.cafe.resources.stock_opening_value
import id.kongstudio.cafe.resources.stock_pick_ingredient
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.ui.component.quantityfield.QuantityField
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.subpageheader.HeaderBack
import id.kongstudio.cafe.ui.component.subpageheader.HeaderWidth
import id.kongstudio.cafe.ui.component.subpageheader.SubPageHeader
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

// Pilihan bahan lebih lebar dari isian angka karena memuat nama bahan.
private const val PickerWeight = 3f
private const val QuantityWeight = 2f

/**
 * Isi stok awal banyak bahan sekaligus, sama dengan dialog isi banyak di web: baris ditambah satu per satu, satu baris satu bahan
 * yang dicari di server, lalu satu konfirmasi dan satu kiriman. Yang tampil hanya bahan yang memang diisi, berapa pun jumlah bahan cabang.
 */
@Composable
internal fun OpeningBulkPage(
    viewModel: OpeningBulkViewModel,
    repository: IngredientStockRepository,
    listTitle: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val spacing = AppTheme.spacing
    val leave = { if (!state.saving) onBack() }
    PlatformBackHandler(enabled = true, onBack = leave)

    Column(modifier = modifier.fillMaxSize()) {
        SubPageHeader(
            title = stringResource(Res.string.stock_opening_bulk),
            back = HeaderBack(stringResource(Res.string.back_to_page, listTitle), leave),
            width = HeaderWidth.Page,
        )
        PageFrame(modifier = Modifier.weight(1f)) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
                    AppText(text = stringResource(Res.string.stock_opening_bulk_hint), role = TextRole.Body)
                    AppText(text = stringResource(Res.string.stock_opening_rule), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                }
            }
            items(state.lines, key = { it.uid }) { line ->
                LineCard(
                    line = line,
                    enabled = !state.saving,
                    onPick = { viewModel.openPicker(line.uid) },
                    onText = { viewModel.setText(line.uid, it) },
                    onRemove = { viewModel.removeLine(line.uid) },
                )
            }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                    if (state.canAddLine) {
                        SecondaryButton(text = stringResource(Res.string.stock_opening_bulk_add_line), onClick = viewModel::addLine, enabled = !state.saving)
                    }
                    state.report?.let { report ->
                        if (report.saved > 0) InlineMessage(text = stringResource(Res.string.stock_opening_bulk_done, report.saved), tone = MessageTone.Success)
                        if (report.failed > 0) InlineMessage(text = stringResource(Res.string.stock_opening_bulk_failed, report.failed))
                    }
                    state.saveFailure?.let { InlineMessage(text = failureText(it)) }
                    val count = state.ready.size
                    PrimaryButton(
                        text = stringResource(Res.string.stock_opening_bulk_save, count),
                        onClick = viewModel::ask,
                        enabled = count > 0 && !state.saving,
                        loading = state.saving,
                    )
                }
            }
        }
    }

    if (state.picking != null) {
        IngredientPicker(repository = repository, onPicked = viewModel::pick, onDismiss = viewModel::closePicker)
    }

    if (state.confirming) {
        val count = state.ready.size
        ConfirmSheet(
            title = stringResource(Res.string.stock_opening_bulk_confirm_title),
            message = stringResource(Res.string.stock_opening_bulk_confirm, count),
            confirmLabel = stringResource(Res.string.stock_opening_bulk_save, count),
            onConfirm = viewModel::save,
            onDismiss = viewModel::dismiss,
            enabled = !state.saving,
        )
    }
}

@Composable
private fun LineCard(line: OpeningLine, enabled: Boolean, onPick: () -> Unit, onText: (String) -> Unit, onRemove: () -> Unit) {
    val spacing = AppTheme.spacing
    val ingredient = line.ingredient
    ListCard {
        Column(modifier = Modifier.fillMaxWidth().padding(spacing.md), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalAlignment = Alignment.Bottom) {
                PickerField(
                    label = stringResource(Res.string.stock_field_ingredient),
                    valueText = ingredient?.name ?: stringResource(Res.string.stock_pick_ingredient),
                    icon = AppIcons.KitchenTools,
                    onClick = onPick,
                    enabled = enabled,
                    modifier = Modifier.weight(PickerWeight),
                )
                QuantityField(
                    value = line.text,
                    onValueChange = onText,
                    label = stringResource(Res.string.stock_opening),
                    unit = ingredient?.unit,
                    isError = line.problem == LineProblem.Quantity || line.problem is LineProblem.Server,
                    enabled = enabled,
                    modifier = Modifier.weight(QuantityWeight),
                )
                AppIconButton(icon = AppIcons.Trash, contentDescription = stringResource(Res.string.stock_opening_bulk_remove_line), onClick = onRemove, tint = AppTheme.colors.danger)
            }
            ingredient?.let {
                val opening = it.opening?.let { value -> stringResource(Res.string.stock_opening_value, StockQuantity.withUnit(value, it.unit)) }
                    ?: stringResource(Res.string.stock_opening_missing)
                AppText(
                    text = "$opening · ${stringResource(Res.string.stock_now, StockQuantity.withUnit(it.stock, it.unit))}",
                    role = TextRole.Caption,
                    color = AppTheme.colors.contentMuted,
                )
            }
            when (val problem = line.problem) {
                LineProblem.NoIngredient -> InlineMessage(text = stringResource(Res.string.stock_opening_bulk_no_ingredient))
                LineProblem.Quantity -> InlineMessage(text = stringResource(Res.string.stock_opening_problem))
                LineProblem.Duplicate -> InlineMessage(text = stringResource(Res.string.stock_opening_bulk_duplicate))
                is LineProblem.Server -> InlineMessage(text = problem.message)
                null -> Unit
            }
        }
    }
}
