package id.kongstudio.cafe.ui.component.loadingstate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.skeleton.SkeletonBlock
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val TitleFraction = 0.6f
private const val CaptionFraction = 0.35f

/** Keadaan memuat berbentuk daftar: kerangka baris yang berkilau, menggantikan spinner. */
@Composable
fun LoadingState(
    modifier: Modifier = Modifier,
    rows: Int = 4,
) {
    val spacing = AppTheme.spacing
    val description = stringResource(Res.string.common_loading)

    ListCard(
        modifier = modifier.semantics {
            contentDescription = description
            liveRegion = LiveRegionMode.Polite
        },
    ) {
        repeat(rows) { index ->
            if (index > 0) AppDivider()
            Row(
                modifier = Modifier.fillMaxWidth().padding(spacing.md),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                SkeletonBlock(
                    modifier = Modifier.size(spacing.compactTarget),
                    shape = AppTheme.shapes.pill,
                )
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(spacing.sm),
                ) {
                    SkeletonBlock(modifier = Modifier.fillMaxWidth(TitleFraction).height(spacing.md))
                    SkeletonBlock(modifier = Modifier.fillMaxWidth(CaptionFraction).height(spacing.md))
                }
            }
        }
    }
}
