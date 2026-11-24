package id.kongstudio.cafe.ui.component.bottombar

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.appicon.AppIcon

class BottomBarItem(
    val label: String,
    val icon: ImageVector,
    val selected: Boolean,
    val onClick: () -> Unit,
    /** Tombol aksi utama: lingkaran primary yang menonjol di atas bilah. */
    val prominent: Boolean = false,
)

/** Bagian lingkaran tombol utama yang berada di atas permukaan bilah. */
private val ProminentOverhang = 22.dp
private val ProminentSize = 56.dp
private val ProminentRing = 3.dp
private val IndicatorWidth = 56.dp
private val IndicatorHeight = 30.dp
private val NoOverhang = 0.dp

@Composable
fun AppBottomBar(
    items: List<BottomBarItem>,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val overhang = if (items.any { it.prominent }) ProminentOverhang else NoOverhang

    Box(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .matchParentSize()
                .padding(top = overhang)
                .background(AppTheme.colors.surface),
        ) {
            AppDivider()
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .windowInsetsPadding(WindowInsets.navigationBars)
                .padding(horizontal = spacing.xs, vertical = spacing.xs),
            verticalAlignment = Alignment.Bottom,
        ) {
            items.forEach { item ->
                BarItem(item = item, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun BarItem(item: BottomBarItem, modifier: Modifier) {
    val colors = AppTheme.colors
    val tint = if (item.selected) colors.primary else colors.contentMuted

    Column(
        modifier = modifier
            .heightIn(min = AppTheme.spacing.touchTarget)
            .clip(if (item.prominent) RectangleShape else AppTheme.shapes.field)
            .selectable(selected = item.selected, role = Role.Tab, onClick = item.onClick)
            .padding(vertical = AppTheme.spacing.xs),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (item.prominent) {
            Box(
                modifier = Modifier
                    .size(ProminentSize)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.background)
                    .padding(ProminentRing)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.primary),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(icon = item.icon, tint = colors.onPrimary, size = AppTheme.sizes.iconLarge)
            }
        } else {
            Box(
                modifier = Modifier
                    .width(IndicatorWidth)
                    .height(IndicatorHeight)
                    .clip(AppTheme.shapes.pill)
                    .background(if (item.selected) colors.selected else Color.Transparent),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(icon = item.icon, tint = tint, size = AppTheme.sizes.icon)
            }
        }
        BasicText(
            text = item.label,
            style = AppTheme.typography.caption.copy(
                color = tint,
                fontWeight = if (item.selected) FontWeight.Bold else FontWeight.Normal,
                textAlign = TextAlign.Center,
            ),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}
