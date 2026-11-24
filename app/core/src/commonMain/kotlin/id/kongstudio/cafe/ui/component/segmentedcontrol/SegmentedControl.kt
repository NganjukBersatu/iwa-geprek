package id.kongstudio.cafe.ui.component.segmentedcontrol

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.selectable
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pilihan satu dari beberapa opsi sejajar; penanda meluncur ke opsi terpilih. */
@Composable
fun SegmentedControl(
    options: List<String>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val inset = AppTheme.spacing.xs
    val shape = AppTheme.shapes.pill
    val position by animateFloatAsState(
        targetValue = selectedIndex.toFloat(),
        animationSpec = tween(AppTheme.effects.standardMillis, easing = AppTheme.effects.bounce),
    )

    BoxWithConstraints(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(colors.surface)
            .padding(inset),
    ) {
        val segment = maxWidth / options.size
        val control = AppTheme.sizes.control

        Box(
            modifier = Modifier
                .offset(x = segment * position)
                .width(segment)
                .height(control)
                .clip(shape)
                .background(colors.primary),
        )
        Row {
            options.forEachIndexed { index, label ->
                Box(
                    modifier = Modifier
                        .width(segment)
                        .height(control)
                        .clip(shape)
                        .selectable(selected = index == selectedIndex, role = Role.Tab, onClick = { onSelect(index) }),
                    contentAlignment = Alignment.Center,
                ) {
                    AppText(
                        text = label,
                        role = TextRole.Label,
                        color = if (index == selectedIndex) colors.onPrimary else colors.content,
                    )
                }
            }
        }
    }
}
