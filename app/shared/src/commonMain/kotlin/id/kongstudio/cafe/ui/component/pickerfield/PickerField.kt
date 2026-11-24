package id.kongstudio.cafe.ui.component.pickerfield

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

/** Kolom isian yang tampil seperti kolom teks tetapi berisi pilihan: ketukannya membuka pemilih, dan [icon] menandai jenisnya. */
@Composable
internal fun PickerField(
    label: String,
    valueText: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field

    Column(modifier) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.content))
        Row(
            modifier = Modifier
                .padding(top = spacing.xs)
                .fillMaxWidth()
                .heightIn(min = spacing.touchTarget)
                .clip(shape)
                .background(colors.surface)
                .border(AppTheme.sizes.borderField, colors.outline, shape)
                .clickable(enabled = enabled, role = Role.Button, onClick = onClick)
                .padding(horizontal = spacing.md),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            BasicText(
                text = valueText,
                style = AppTheme.typography.body.copy(color = colors.content),
                modifier = Modifier.weight(1f),
            )
            AppIcon(icon = icon, tint = colors.primary, size = AppTheme.sizes.icon)
        }
    }
}
