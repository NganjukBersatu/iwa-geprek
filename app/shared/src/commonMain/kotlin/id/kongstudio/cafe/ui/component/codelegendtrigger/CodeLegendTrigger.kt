package id.kongstudio.cafe.ui.component.codelegendtrigger

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.codelegend.CodeLegend
import id.kongstudio.cafe.ui.component.codelegend.CodeLegendItem
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Baris ikon dan judul yang membuka lembar berisi [CodeLegend], supaya daftarnya tidak memenuhi halaman. */
@Composable
fun CodeLegendTrigger(
    title: String,
    items: List<CodeLegendItem>,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var open by remember { mutableStateOf(false) }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(role = Role.Button) { open = true }
            .padding(horizontal = spacing.sm, vertical = spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        AppIcon(icon = AppIcons.Info, tint = colors.primary, size = AppTheme.sizes.icon)
        BasicText(text = title, style = AppTheme.typography.label.copy(color = colors.primary))
    }

    if (open) {
        AppBottomSheet(title = title, onDismiss = { open = false }) {
            CodeLegend(items = items, modifier = Modifier.padding(bottom = spacing.lg))
        }
    }
}
