package id.kongstudio.cafe.ui.component.monthpicker

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.month_picker_next
import id.kongstudio.cafe.resources.month_picker_previous
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.component.appicon.AppIcon

@Composable
fun MonthPicker(
    label: String,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    nextEnabled: Boolean,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.field

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(colors.surface)
            .border(AppTheme.sizes.borderThin, colors.divider, shape),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        PickerButton(
            AppIcons.ChevronLeft,
            stringResource(Res.string.month_picker_previous),
            enabled = true,
            onClick = onPrevious,
        )
        BasicText(
            text = label,
            style = AppTheme.typography.button.copy(color = colors.content, textAlign = TextAlign.Center),
            modifier = Modifier.weight(1f),
        )
        PickerButton(
            AppIcons.ChevronRight,
            stringResource(Res.string.month_picker_next),
            enabled = nextEnabled,
            onClick = onNext,
        )
    }
}

@Composable
private fun PickerButton(
    icon: ImageVector,
    description: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Box(
        modifier = Modifier
            .size(AppTheme.spacing.touchTarget)
            .alpha(if (enabled) 1f else AppTheme.colors.disabledAlpha)
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = icon, tint = AppTheme.colors.primary, size = AppTheme.sizes.icon, contentDescription = description)
    }
}
