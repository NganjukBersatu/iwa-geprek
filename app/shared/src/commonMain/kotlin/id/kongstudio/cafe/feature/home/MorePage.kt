package id.kongstudio.cafe.feature.home

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.cardgrid.CardGrid
import id.kongstudio.cafe.ui.component.featurecard.FeatureCard
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Halaman Lainnya: kisi kartu fitur dua kolom yang selalu muat satu layar. */
@Composable
internal fun MorePage(
    cards: List<MoreCard>,
    onSelect: (HomePage) -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = AppTheme.windowSize.pagePadding),
        contentAlignment = Alignment.TopCenter,
    ) {
        CardGrid(
            items = cards,
            modifier = Modifier
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .padding(vertical = AppTheme.spacing.sm),
        ) { card ->
            FeatureCard(
                title = stringResource(card.title),
                icon = card.icon,
                decoration = card.decoration,
                tone = card.tone,
                onClick = { onSelect(card.target) },
            )
        }
    }
}
