package id.kongstudio.cafe.ui.component.ratingcard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.ratingstars.RatingStars
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private const val ChevronOpenDegrees = 180f

/**
 * Kartu bintang: [stars] dan [valueText] selalu tampak, dan [details] terbuka halus di bawahnya saat kartu diketuk;
 * tanpa [details] kartu tidak bisa dibuka.
 */
@Composable
fun RatingCard(
    stars: Float,
    valueText: String,
    starsDescription: String,
    openLabel: String,
    closeLabel: String,
    modifier: Modifier = Modifier,
    details: (@Composable ColumnScope.() -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val effects = AppTheme.effects
    var open by remember { mutableStateOf(false) }
    val turn by animateFloatAsState(
        targetValue = if (open) ChevronOpenDegrees else 0f,
        animationSpec = tween(effects.standardMillis, easing = effects.standard),
        label = "rating-chevron",
    )

    ListCard(modifier = modifier) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .then(
                    if (details != null) {
                        Modifier.clickable(onClickLabel = if (open) closeLabel else openLabel, role = Role.Button) { open = !open }
                    } else {
                        Modifier
                    },
                )
                .padding(spacing.md),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            RatingStars(stars = stars, description = starsDescription)
            BasicText(
                text = valueText,
                style = AppTheme.typography.body.copy(color = colors.content),
                modifier = Modifier.weight(1f),
            )
            if (details != null) {
                AppIcon(
                    icon = AppIcons.ChevronDown,
                    tint = colors.contentMuted,
                    size = AppTheme.sizes.iconSmall,
                    modifier = Modifier.graphicsLayer { rotationZ = turn },
                )
            }
        }
        if (details != null) {
            AnimatedVisibility(
                visible = open,
                enter = expandVertically(tween(effects.standardMillis, easing = effects.standard)) +
                    fadeIn(tween(effects.standardMillis)),
                exit = shrinkVertically(tween(effects.standardMillis, easing = effects.standard)) +
                    fadeOut(tween(effects.quickMillis)),
            ) {
                Column {
                    AppDivider()
                    details()
                }
            }
        }
    }
}
