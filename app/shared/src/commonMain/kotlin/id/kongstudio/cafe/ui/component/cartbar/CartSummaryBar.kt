package id.kongstudio.cafe.ui.component.cartbar

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Ringkasan keranjang di bawah daftar menu pada layar sempit. */
@Composable
fun CartSummaryBar(
    countLabel: String,
    totalLabel: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val textStyle = AppTheme.typography.button.copy(color = colors.onPrimary)

    Row(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = AppTheme.spacing.touchTarget)
            .clip(AppTheme.shapes.pill)
            .background(colors.primary)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = AppTheme.spacing.lg, vertical = AppTheme.spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        BasicText(text = countLabel, style = textStyle)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
        ) {
            BasicText(text = totalLabel, style = textStyle)
            AppIcon(icon = AppIcons.ChevronRight, tint = colors.onPrimary, size = AppTheme.sizes.iconSmall)
        }
    }
}
