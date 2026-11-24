package id.kongstudio.cafe.ui.component.loadable

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.skeleton.SkeletonBlock
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val CardHeightFactor = 3
private const val BoardColumns = 3
private const val BoardCardsPerColumn = 3
private const val MaxCardColumns = 4
private const val CardRows = 3
private const val DetailLines = 4
private const val HeaderFraction = 0.45f
private const val LineFraction = 0.8f

/** Kerangka tiap [LoadingVariant]; daftar memakai [LoadingState] yang sudah ada. */
@Composable
internal fun LoadingSkeleton(variant: LoadingVariant, rows: Int, modifier: Modifier = Modifier) {
    val description = stringResource(Res.string.common_loading)
    val spacing = AppTheme.spacing

    when (variant) {
        LoadingVariant.List -> LoadingState(modifier = modifier, rows = rows)

        LoadingVariant.Cards -> BoxWithConstraints(
            modifier = modifier.fillMaxWidth().semantics { announce(description) },
        ) {
            val columns = (maxWidth / AppTheme.sizes.sidePanelWidth).toInt().coerceIn(1, MaxCardColumns)
            Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                repeat(CardRows) {
                    Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                        repeat(columns) {
                            SkeletonBlock(
                                modifier = Modifier
                                    .weight(1f)
                                    .height(spacing.compactTarget * CardHeightFactor),
                                shape = AppTheme.shapes.card,
                            )
                        }
                    }
                }
            }
        }

        LoadingVariant.Board -> Row(
            modifier = modifier.fillMaxSize().semantics { announce(description) },
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            repeat(BoardColumns) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
                    SkeletonBlock(modifier = Modifier.fillMaxWidth(HeaderFraction).height(spacing.lg))
                    repeat(BoardCardsPerColumn) {
                        SkeletonBlock(
                            modifier = Modifier.fillMaxWidth().height(spacing.compactTarget * CardHeightFactor),
                            shape = AppTheme.shapes.card,
                        )
                    }
                }
            }
        }

        LoadingVariant.Detail -> Column(
            modifier = modifier.fillMaxWidth().semantics { announce(description) },
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            SkeletonBlock(modifier = Modifier.fillMaxWidth(HeaderFraction).height(spacing.xl))
            repeat(DetailLines) { index ->
                SkeletonBlock(
                    modifier = Modifier
                        .fillMaxWidth(if (index == DetailLines - 1) HeaderFraction else LineFraction)
                        .height(spacing.md),
                )
            }
        }
    }
}

private fun androidx.compose.ui.semantics.SemanticsPropertyReceiver.announce(description: String) {
    contentDescription = description
    liveRegion = LiveRegionMode.Polite
}
