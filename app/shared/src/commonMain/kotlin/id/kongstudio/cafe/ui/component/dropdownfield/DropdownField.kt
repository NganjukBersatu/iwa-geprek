package id.kongstudio.cafe.ui.component.dropdownfield

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.ui.component.progressline.ProgressLine
import id.kongstudio.cafe.ui.component.scrollend.OnScrollEnd
import id.kongstudio.cafe.ui.component.searchfield.SearchField
import id.kongstudio.cafe.ui.component.skeleton.SkeletonRows
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private val ListMaxHeight = 220.dp
private const val SearchSkeletonRows = 3
private const val MoreSkeletonRows = 2

/** Satu pilihan dropdown; [key] null berarti "semua" atau "tanpa pilihan". */
internal class DropdownOption(val key: String?, val label: String)

/** Kolom pilihan yang membuka daftar di tempatnya dan langsung memanggil [onSelect], bisa disaring bila [searchLabel] diisi, dan menambah kata baru lewat baris [addLabel] bila [onAdd] ada. */
@Composable
internal fun DropdownField(
    label: String,
    options: List<DropdownOption>,
    selectedKey: String?,
    onSelect: (String?) -> Unit,
    modifier: Modifier = Modifier,
    searchLabel: String? = null,
    emptyText: String = "",
    addLabel: @Composable (String) -> String = { it },
    onAdd: ((String) -> Unit)? = null,
    searchMaxLength: Int = Int.MAX_VALUE,
    /** Bila diisi, daftar disaring oleh pemanggil (misalnya di server) dan [options] ditampilkan apa adanya. */
    onQueryChange: ((String) -> Unit)? = null,
    /** Dipanggil saat daftar digulir mendekati akhir, supaya pemanggil memuat halaman berikutnya. */
    onReachEnd: (() -> Unit)? = null,
    /** Hasil cari sedang ditunggu dari pemanggil: daftar diganti kerangka di bawah garis progres. */
    searching: Boolean = false,
    /** Halaman berikutnya sedang dimuat: kerangka di ujung bawah daftar dan garis progres. */
    loadingMore: Boolean = false,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var open by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf("") }
    val selected = options.firstOrNull { it.key == selectedKey } ?: options.first()
    val typed = query.trim()
    val shown = if (typed.isEmpty() || onQueryChange != null) options else options.filter { it.label.contains(typed, ignoreCase = true) }
    val addable = onAdd != null && typed.isNotEmpty() && options.none { it.label.equals(typed, ignoreCase = true) }

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        PickerField(
            label = label,
            valueText = selected.label,
            icon = if (open) AppIcons.ChevronUp else AppIcons.ChevronDown,
            onClick = {
                open = !open
                query = ""
                onQueryChange?.invoke("")
            },
        )
        if (open) {
            if (searchLabel != null) {
                SearchField(
                    value = query,
                    onValueChange = {
                        if (it.length <= searchMaxLength) {
                            query = it
                            onQueryChange?.invoke(it.trim())
                        }
                    },
                    label = searchLabel,
                )
            }
            val scroll = rememberScrollState()
            if (onReachEnd != null) OnScrollEnd(scroll = scroll, count = options.size, onEnd = onReachEnd)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(AppTheme.shapes.field)
                    .background(colors.surface)
                    .border(AppTheme.sizes.borderThin, colors.divider, AppTheme.shapes.field),
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = ListMaxHeight)
                        .verticalScroll(scroll),
                ) {
                    when {
                        searching -> SkeletonRows(count = SearchSkeletonRows, modifier = Modifier.padding(spacing.sm))
                        shown.isEmpty() && !addable -> BasicText(
                            text = emptyText,
                            style = AppTheme.typography.body.copy(color = colors.contentMuted),
                            modifier = Modifier.padding(spacing.md),
                        )
                        else -> shown.forEach { option ->
                            OptionRow(
                                option = option,
                                selected = option.key == selectedKey,
                                onClick = {
                                    onSelect(option.key)
                                    open = false
                                    query = ""
                                },
                            )
                        }
                    }
                    if (loadingMore) SkeletonRows(count = MoreSkeletonRows, modifier = Modifier.padding(spacing.sm))
                    if (addable && !searching) {
                        AddRow(
                            label = addLabel(typed),
                            onClick = {
                                onAdd?.invoke(typed)
                                open = false
                                query = ""
                            },
                        )
                    }
                }
                // Garis ditumpuk di atas daftar, supaya muncul dan hilangnya tidak menggeser pilihan.
                if (searching || loadingMore) ProgressLine(modifier = Modifier.align(Alignment.TopCenter))
            }
        }
    }
}

@Composable
private fun AddRow(label: String, onClick: () -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = spacing.touchTarget)
            .background(colors.surface)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        AppIcon(icon = AppIcons.Plus, tint = colors.primary, size = AppTheme.sizes.iconSmall)
        BasicText(
            text = label,
            style = AppTheme.typography.body.copy(color = colors.primary),
            modifier = Modifier.weight(1f),
        )
    }
}

@Composable
private fun OptionRow(option: DropdownOption, selected: Boolean, onClick: () -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = spacing.touchTarget)
            .background(if (selected) colors.selected else colors.surface)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        BasicText(
            text = option.label,
            style = AppTheme.typography.body.copy(color = colors.content),
            modifier = Modifier.weight(1f),
        )
        if (selected) AppIcon(icon = AppIcons.Check, tint = colors.primary, size = AppTheme.sizes.iconSmall)
    }
}
