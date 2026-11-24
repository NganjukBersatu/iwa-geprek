package id.kongstudio.cafe.feature.ingredientstock

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.stock_low
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.productcard.BlockedLabel
import id.kongstudio.cafe.ui.component.productcard.BlockedTone
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/**
 * Satu baris bahan untuk semua daftar bahan tablet: ikon, nama dengan [caption], stok ditonjolkan di kanan
 * (merah bila minus, kuning bila di bawah minimum), dan chevron karena baris membuka rincian; [status] lencana tambahan khusus layar pemakai.
 */
@Composable
internal fun IngredientRow(
    ingredient: StockIngredient,
    caption: String?,
    onClick: () -> Unit,
    status: (@Composable () -> Unit)? = null,
    leading: @Composable () -> Unit = { IconBadge(AppIcons.KitchenTools) },
) {
    val colors = AppTheme.colors
    ListRow(
        title = ingredient.name,
        caption = caption,
        badge = if (ingredient.low || status != null) {
            {
                Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
                    status?.invoke()
                    if (ingredient.low) BlockedLabel(text = stringResource(Res.string.stock_low), tone = BlockedTone.Warning)
                }
            }
        } else {
            null
        },
        leading = leading,
        trailing = {
            AppText(
                text = StockQuantity.withUnit(ingredient.stock, ingredient.unit),
                role = TextRole.Subtitle,
                color = when {
                    StockQuantity.isNegative(ingredient.stock) -> colors.danger
                    ingredient.low -> colors.warning
                    else -> colors.content
                },
            )
        },
        onClick = onClick,
        opensDetail = true,
    )
}
