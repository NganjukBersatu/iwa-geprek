package id.kongstudio.cafe.ui.component.filterbar

import androidx.compose.foundation.clickable
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.filter_button
import id.kongstudio.cafe.resources.filter_button_count
import id.kongstudio.cafe.resources.filter_clear_all
import id.kongstudio.cafe.resources.filter_close
import id.kongstudio.cafe.resources.filter_remove
import id.kongstudio.cafe.resources.filter_reset
import id.kongstudio.cafe.resources.filter_title
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.searchfield.SearchField
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import org.jetbrains.compose.resources.stringResource

private val FilterButtonWidth = 144.dp

/** Satu filter yang sedang aktif: [label] tampil di tag dan [onRemove] mengembalikan filter itu ke bawaan. */
internal class FilterTag(val label: String, val onRemove: () -> Unit)

/**
 * Satu komponen filter untuk semua daftar: kolom cari dan satu tombol Filter di satu baris, lalu tag filter aktif
 * dengan "Hapus semua filter". Isi filter ([sheetContent]) membuka lembar yang langsung berlaku, tanpa tombol terapkan.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun FilterBar(
    searchLabel: String?,
    query: String,
    onQueryChange: (String) -> Unit,
    showButton: Boolean,
    tags: List<FilterTag>,
    onClearAll: () -> Unit,
    modifier: Modifier = Modifier,
    /** Judul bagian di kiri tombol Filter bila tanpa kolom cari, supaya tombol tidak mengambang sendirian. */
    leadingTitle: String? = null,
    leadingRole: TextRole = TextRole.Label,
    sheetContent: @Composable ColumnScope.() -> Unit,
) {
    val spacing = AppTheme.spacing
    var open by rememberSaveable { mutableStateOf(false) }

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            verticalAlignment = if (searchLabel != null) Alignment.Bottom else Alignment.CenterVertically,
        ) {
            when {
                searchLabel != null -> SearchField(value = query, onValueChange = onQueryChange, label = searchLabel, modifier = Modifier.weight(1f))
                leadingTitle != null -> AppText(text = leadingTitle, role = leadingRole, modifier = Modifier.weight(1f))
                else -> Spacer(Modifier.weight(1f))
            }
            if (showButton) {
                SecondaryButton(
                    text = if (tags.isEmpty()) stringResource(Res.string.filter_button) else stringResource(Res.string.filter_button_count, tags.size),
                    onClick = { open = true },
                    modifier = Modifier.width(FilterButtonWidth),
                )
            }
        }
        if (tags.isNotEmpty()) {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalArrangement = Arrangement.spacedBy(spacing.xs), itemVerticalAlignment = Alignment.CenterVertically) {
                tags.forEach { tag -> FilterTagChip(tag) }
                ClearAllText(onClick = onClearAll)
            }
        }
    }

    if (open) {
        AppBottomSheet(title = stringResource(Res.string.filter_title), onDismiss = { open = false }) {
            Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
                sheetContent()
                PrimaryButton(text = stringResource(Res.string.filter_close), onClick = { open = false })
                SecondaryButton(
                    text = stringResource(Res.string.filter_reset),
                    onClick = onClearAll,
                    tone = ButtonTone.Danger,
                    enabled = tags.isNotEmpty(),
                    modifier = Modifier.padding(bottom = spacing.sm),
                )
            }
        }
    }
}

@Composable
private fun FilterTagChip(tag: FilterTag) {
    val colors = AppTheme.colors
    Row(
        modifier = Modifier
            .heightIn(min = AppTheme.sizes.control)
            .clip(AppTheme.shapes.pill)
            .background(colors.primary)
            .clickable(role = Role.Button, onClick = tag.onRemove)
            .padding(horizontal = AppTheme.spacing.lg),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        BasicText(text = tag.label, style = AppTheme.typography.label.copy(color = colors.onPrimary))
        AppIcon(
            icon = AppIcons.Close,
            tint = colors.onPrimary,
            size = AppTheme.sizes.iconSmall,
            contentDescription = stringResource(Res.string.filter_remove, tag.label),
        )
    }
}

/** Menghapus semua filter sekaligus; berwarna bahaya karena menghapus pilihan pengguna, dan teksnya di tengah area sentuh supaya sejajar dengan tag. */
@Composable
private fun ClearAllText(onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .heightIn(min = AppTheme.spacing.touchTarget)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = AppTheme.spacing.sm),
        contentAlignment = Alignment.Center,
    ) {
        BasicText(
            text = stringResource(Res.string.filter_clear_all),
            style = AppTheme.typography.label.copy(color = AppTheme.colors.danger),
        )
    }
}
