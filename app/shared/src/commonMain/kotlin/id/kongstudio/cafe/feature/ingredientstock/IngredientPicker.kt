package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.feature.admin.rememberChoicePages
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.stock_now
import id.kongstudio.cafe.resources.stock_pick_empty
import id.kongstudio.cafe.resources.stock_pick_title
import id.kongstudio.cafe.resources.stock_search
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.scrollend.OnScrollEnd
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val SearchSkeletonRows = 4
private const val MoreSkeletonRows = 2

/** Memilih satu bahan dengan pencarian nama; dipakai semua layar yang mencatat atau menghitung stok. */
@Composable
internal fun IngredientPicker(repository: IngredientStockRepository, onPicked: (StockIngredient) -> Unit, onDismiss: () -> Unit, indirectOnly: Boolean = false) {
    var query by remember { mutableStateOf("") }
    val choices = rememberChoicePages<StockIngredient>(key = { it.id }, fetch = { query, page -> repository.ingredientChoices(query, page, indirectOnly) })
    val scroll = rememberScrollState()
    OnScrollEnd(scroll = scroll, count = choices.items.size, onEnd = choices::more)

    AppBottomSheet(title = stringResource(Res.string.stock_pick_title), onDismiss = onDismiss, scroll = scroll, busy = choices.busy) {
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppTextField(
                value = query,
                onValueChange = {
                    query = it
                    choices.search(it)
                },
                label = stringResource(Res.string.stock_search),
            )
            choices.failure?.let { BasicText(text = failureText(it), style = AppTheme.typography.caption.copy(color = AppTheme.colors.danger)) }
            if (choices.searching) {
                SkeletonRows(count = SearchSkeletonRows)
                return@Column
            }
            if (choices.failure == null && choices.items.isEmpty()) {
                BasicText(text = stringResource(Res.string.stock_pick_empty), style = AppTheme.typography.caption.copy(color = AppTheme.colors.contentMuted))
            }
            choices.items.forEach { ingredient ->
                ListRow(
                    title = ingredient.name,
                    detail = stringResource(Res.string.stock_now, StockQuantity.withUnit(ingredient.stock, ingredient.unit)),
                    onClick = { onPicked(ingredient) },
                )
            }
            if (choices.loadingMore) SkeletonRows(count = MoreSkeletonRows)
        }
    }
}
