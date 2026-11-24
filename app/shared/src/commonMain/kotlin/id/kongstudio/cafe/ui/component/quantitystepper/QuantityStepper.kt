package id.kongstudio.cafe.ui.component.quantitystepper

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.quantity_decrease
import id.kongstudio.cafe.resources.quantity_increase
import id.kongstudio.cafe.resources.quantity_remove
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import org.jetbrains.compose.resources.stringResource

/**
 * Pengatur jumlah; bila [removable], tombol kiri berubah menjadi hapus pada jumlah 1,
 * selain itu jumlah bisa turun sampai 0 dan tombol kurangi redup di angka 0.
 */
@Composable
fun QuantityStepper(
    quantity: Int,
    onDecrease: () -> Unit,
    onIncrease: () -> Unit,
    modifier: Modifier = Modifier,
    removable: Boolean = true,
) {
    val colors = AppTheme.colors
    val removing = removable && quantity <= 1
    val atZero = !removable && quantity <= 0

    Row(modifier = modifier, verticalAlignment = Alignment.CenterVertically) {
        StepperButton(
            icon = if (removing) AppIcons.Trash else AppIcons.Minus,
            description = stringResource(if (removing) Res.string.quantity_remove else Res.string.quantity_decrease),
            tint = when {
                removing -> colors.danger
                atZero -> colors.contentMuted
                else -> colors.primary
            },
            onClick = onDecrease,
            enabled = !atZero,
        )
        BasicText(
            text = quantity.toString(),
            style = AppTheme.typography.button.copy(color = colors.content, textAlign = TextAlign.Center),
            modifier = Modifier.widthIn(min = AppTheme.sizes.icon),
        )
        StepperButton(
            icon = AppIcons.Plus,
            description = stringResource(Res.string.quantity_increase),
            tint = colors.primary,
            onClick = onIncrease,
        )
    }
}

@Composable
private fun StepperButton(
    icon: ImageVector,
    description: String,
    tint: Color,
    onClick: () -> Unit,
    enabled: Boolean = true,
) {
    Box(
        modifier = Modifier
            .size(AppTheme.sizes.control)
            .clip(AppTheme.shapes.pill)
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .size(AppTheme.sizes.controlSmall)
                .clip(AppTheme.shapes.pill)
                .background(AppTheme.colors.selected),
            contentAlignment = Alignment.Center,
        ) {
            AppIcon(icon = icon, tint = tint, size = AppTheme.sizes.iconSmall, contentDescription = description)
        }
    }
}
