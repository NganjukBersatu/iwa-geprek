package id.kongstudio.cafe.ui.component.chip

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

/** Satu pilihan berbentuk pil; [icon] opsional di depan label, [shape] diganti hanya oleh kisi pilihan. */
@Composable
fun AppChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    shape: Shape = AppTheme.shapes.pill,
) {
    val colors = AppTheme.colors

    Box(
        modifier = modifier
            .heightIn(min = AppTheme.sizes.control)
            .clip(shape)
            .background(if (selected) colors.primary else colors.surface)
            .border(AppTheme.sizes.borderThin, if (selected) colors.primary else colors.outline, shape)
            .selectable(selected = selected, role = Role.Tab, onClick = onClick)
            .padding(horizontal = AppTheme.spacing.lg),
        contentAlignment = Alignment.Center,
    ) {
        val tint = if (selected) colors.onPrimary else colors.content
        Row(
            horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            icon?.let { AppIcon(icon = it, tint = tint, size = AppTheme.sizes.iconSmall) }
            BasicText(text = label, style = AppTheme.typography.label.copy(color = tint, textAlign = TextAlign.Center))
        }
    }
}
