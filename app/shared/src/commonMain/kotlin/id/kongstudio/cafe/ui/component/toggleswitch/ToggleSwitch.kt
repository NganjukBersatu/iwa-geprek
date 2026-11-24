package id.kongstudio.cafe.ui.component.toggleswitch

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.ui.theme.AppTheme

/** Saklar nyala-mati dengan [label] di kirinya; seluruh baris bisa diketuk. */
@Composable
fun ToggleSwitch(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
    /** Nama untuk pembaca layar bila [label] kosong, misalnya saklar di dalam baris daftar. */
    accessibleName: String = label,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val trackWidth = spacing.xxxl
    val trackHeight = spacing.xl + spacing.xs
    val thumb = spacing.xl
    val inset = (trackHeight - thumb) / 2
    val thumbOffset by animateDpAsState(if (checked) trackWidth - thumb - inset else inset)

    Row(
        modifier = modifier
            .heightIn(min = spacing.touchTarget)
            .toggleable(value = checked, role = Role.Switch, onValueChange = onCheckedChange)
            .semantics { if (accessibleName.isNotBlank()) contentDescription = accessibleName },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.content))
        Box(
            modifier = Modifier
                .width(trackWidth)
                .height(trackHeight)
                .clip(AppTheme.shapes.pill)
                .background(if (checked) colors.primary else colors.outline.copy(alpha = colors.disabledAlpha)),
            contentAlignment = Alignment.CenterStart,
        ) {
            Box(
                modifier = Modifier
                    .offset(x = thumbOffset)
                    .size(thumb)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.onPrimary),
            )
        }
    }
}
