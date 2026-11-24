package id.kongstudio.cafe.ui.component.statcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.centeredstat.CenteredStat
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.theme.AppTheme

/** Kartu angka: dengan [icon] ikon sejajar label, dengan [iconBeside] ikon di kiri dan label serta angka bertumpuk di kanannya, dengan [centered] semuanya bertumpuk rata tengah. */
@Composable
fun StatCard(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueColor: Color = AppTheme.colors.content,
    icon: ImageVector? = null,
    iconBeside: Boolean = false,
    centered: Boolean = false,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    val frame = modifier
        .fillMaxWidth()
        .clip(shape)
        .background(colors.surface)
        .border(AppTheme.sizes.borderThin, colors.divider, shape)
        .padding(spacing.md)
    val labelStyle = AppTheme.typography.caption.copy(color = colors.contentMuted)
    val valueStyle = AppTheme.typography.title.copy(color = valueColor)

    when {
        centered -> Column(modifier = frame, verticalArrangement = Arrangement.Center) {
            CenteredStat(label = label, value = value, icon = icon, valueColor = valueColor)
        }

        icon != null && iconBeside -> Row(
            modifier = frame,
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            IconBadge(icon)
            Column {
                BasicText(text = label, style = labelStyle)
                BasicText(text = value, style = valueStyle, maxLines = 1)
            }
        }

        icon != null -> Column(modifier = frame, verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                IconBadge(icon)
                BasicText(text = label, style = labelStyle)
            }
            BasicText(text = value, style = valueStyle)
        }

        else -> Column(modifier = frame) {
            BasicText(text = label, style = labelStyle)
            BasicText(text = value, style = valueStyle)
        }
    }
}
