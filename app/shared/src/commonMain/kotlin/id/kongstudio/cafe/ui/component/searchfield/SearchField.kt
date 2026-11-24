package id.kongstudio.cafe.ui.component.searchfield

import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Kolom pencarian: kolom teks dengan ikon kaca pembesar di ujung kanan. */
@Composable
fun SearchField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
) {
    AppTextField(
        value = value,
        onValueChange = onValueChange,
        label = label,
        modifier = modifier,
        trailing = {
            AppIcon(
                icon = AppIcons.Search,
                tint = AppTheme.colors.contentMuted,
                size = AppTheme.sizes.iconSmall,
                modifier = Modifier.padding(end = AppTheme.spacing.md),
            )
        },
    )
}
