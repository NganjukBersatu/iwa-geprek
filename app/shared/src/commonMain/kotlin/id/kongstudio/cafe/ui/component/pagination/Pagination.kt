package id.kongstudio.cafe.ui.component.pagination

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.pagination_back
import id.kongstudio.cafe.resources.pagination_jump
import id.kongstudio.cafe.resources.pagination_next
import id.kongstudio.cafe.resources.pagination_next_description
import id.kongstudio.cafe.resources.pagination_previous_description
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Jumlah slot minimum agar daftar nomor dengan celah (1 2 3 … 12) layak ditampilkan. */
private const val MinSlotsForNumbers = 6

/** Pengatur halaman satu baris: kolom lompat di kiri dan nomor di kanan yang menyesuaikan lebar (jatuh ke "n / total" bila sempit), dengan [page] berbasis nol. */
@Composable
fun Pagination(
    page: Int,
    pageCount: Int,
    onPageChange: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val jumpWidth = spacing.touchTarget * 1.75f
    val slotWidth = spacing.compactTarget + spacing.xs

    BoxWithConstraints(modifier = modifier.fillMaxWidth().padding(spacing.sm)) {
        val stepWidth = spacing.compactTarget
        val slots = ((maxWidth - jumpWidth - stepWidth * 2 - spacing.md) / slotWidth).toInt()

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            JumpField(width = jumpWidth, pageCount = pageCount, onJump = onPageChange)
            Row(verticalAlignment = Alignment.CenterVertically) {
                StepButton(
                    label = stringResource(Res.string.pagination_back).takeIf { AppTheme.windowSize.isWide },
                    description = stringResource(Res.string.pagination_previous_description),
                    leading = true,
                    enabled = page > 0,
                ) { onPageChange(page - 1) }

                if (slots >= MinSlotsForNumbers || pageCount <= slots) {
                    pageItems(current = page, count = pageCount).forEach { item ->
                        if (item == null) {
                            BasicText(
                                text = "…",
                                style = AppTheme.typography.body.copy(color = AppTheme.colors.contentMuted),
                                modifier = Modifier.padding(horizontal = spacing.xs),
                            )
                        } else {
                            PageChip(number = item + 1, selected = item == page) { onPageChange(item) }
                        }
                    }
                } else {
                    BasicText(
                        text = "${page + 1} / $pageCount",
                        style = AppTheme.typography.label.copy(color = AppTheme.colors.content),
                        modifier = Modifier.padding(horizontal = spacing.sm),
                    )
                }

                StepButton(
                    label = stringResource(Res.string.pagination_next).takeIf { AppTheme.windowSize.isWide },
                    description = stringResource(Res.string.pagination_next_description),
                    leading = false,
                    enabled = page < pageCount - 1,
                ) { onPageChange(page + 1) }
            }
        }
    }
}

/** Indeks halaman yang tampil, dengan null menandai celah dan selalu memuat pertama, terakhir, dan sekitar [current]. */
internal fun pageItems(current: Int, count: Int): List<Int?> {
    if (count <= 6) return (0 until count).toList()
    val shown = sortedSetOf(0, count - 1, current - 1, current, current + 1)
    if (current <= 1) shown += 2
    if (current >= count - 2) shown += count - 3
    val result = mutableListOf<Int?>()
    var previous = -1
    shown.filter { it in 0 until count }.forEach { index ->
        if (previous != -1 && index - previous > 1) result += null
        result += index
        previous = index
    }
    return result
}

@Composable
private fun PageChip(number: Int, selected: Boolean, onClick: () -> Unit) {
    val colors = AppTheme.colors

    // Area ketuk setinggi target sentuh; tampilan nomor tetap ringkas.
    Box(
        modifier = Modifier
            .padding(horizontal = AppTheme.spacing.xs / 2)
            .width(AppTheme.spacing.compactTarget)
            .heightIn(min = AppTheme.spacing.touchTarget)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .size(AppTheme.spacing.compactTarget)
                .clip(AppTheme.shapes.field)
                .background(if (selected) colors.primary else colors.selected),
            contentAlignment = Alignment.Center,
        ) {
            BasicText(
                text = number.toString(),
                style = AppTheme.typography.label.copy(
                    color = if (selected) colors.onPrimary else colors.content,
                    textAlign = TextAlign.Center,
                ),
            )
        }
    }
}

@Composable
private fun StepButton(
    label: String?,
    description: String,
    leading: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = Modifier
            .heightIn(min = spacing.touchTarget)
            .alpha(if (enabled) 1f else AppTheme.colors.disabledAlpha)
            .clip(AppTheme.shapes.field)
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center,
    ) {
        if (!leading && label != null) {
            BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.primary))
        }
        AppIcon(icon = if (leading) AppIcons.ChevronLeft else AppIcons.ChevronRight, tint = colors.primary, size = spacing.compactTarget / 2, contentDescription = description)
        if (leading && label != null) {
            BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.primary))
        }
    }
}

@Composable
private fun JumpField(width: androidx.compose.ui.unit.Dp, pageCount: Int, onJump: (Int) -> Unit) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.field
    var text by remember { mutableStateOf("") }

    fun jump() {
        text.toIntOrNull()?.let { onJump(it.coerceIn(1, pageCount) - 1) }
        text = ""
    }

    BasicTextField(
        value = text,
        onValueChange = { value -> text = value.filter { it.isDigit() }.take(4) },
        singleLine = true,
        textStyle = AppTheme.typography.body.copy(color = colors.content, textAlign = TextAlign.Center),
        cursorBrush = SolidColor(colors.primary),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Go),
        keyboardActions = KeyboardActions(onGo = { jump() }),
        decorationBox = { inner ->
            Box(
                modifier = Modifier
                    .width(width)
                    .heightIn(min = AppTheme.spacing.compactTarget)
                    .clip(shape)
                    .background(colors.surface)
                    .border(AppTheme.sizes.borderThin, colors.outline, shape)
                    .padding(horizontal = AppTheme.spacing.sm),
                contentAlignment = Alignment.Center,
            ) {
                if (text.isEmpty()) {
                    BasicText(
                        text = stringResource(Res.string.pagination_jump),
                        style = AppTheme.typography.caption.copy(color = colors.contentMuted),
                    )
                }
                inner()
            }
        },
    )
}
