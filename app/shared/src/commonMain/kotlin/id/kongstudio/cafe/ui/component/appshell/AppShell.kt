package id.kongstudio.cafe.ui.component.appshell

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalDensity
import id.kongstudio.cafe.ui.component.slidingrail.SlidingRail
import id.kongstudio.cafe.ui.theme.AppTheme


/** Kerangka halaman setelah login: bilah bawah di HP dan rail kiri di layar lebar, yang dengan [slidingRail] meluncur lewat satu gagang tanpa mode ciut. */
@Composable
fun AppShell(
    bottomBar: @Composable () -> Unit,
    rail: @Composable ColumnScope.(collapsed: Boolean, onToggle: () -> Unit) -> Unit,
    modifier: Modifier = Modifier,
    slidingRail: Boolean = false,
    hideRailDescription: String = "",
    showRailDescription: String = "",
    content: @Composable () -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    if (AppTheme.windowSize.isWide && slidingRail) {
        SlidingRail(
            hideDescription = hideRailDescription,
            showDescription = showRailDescription,
            rail = { rail(false) {} },
            modifier = modifier,
            content = content,
        )
    } else if (AppTheme.windowSize.isWide) {
        var collapsed by rememberSaveable { mutableStateOf(false) }
        val width by animateDpAsState(if (collapsed) AppTheme.sizes.railCollapsedWidth else AppTheme.sizes.railWidth)

        Row(
            modifier = modifier
                .fillMaxSize()
                .background(colors.background)
                .windowInsetsPadding(WindowInsets.systemBars.only(WindowInsetsSides.Vertical)),
        ) {
            Column(
                modifier = Modifier
                    .padding(spacing.sm)
                    .width(width)
                    .fillMaxHeight()
                    .clip(AppTheme.shapes.card)
                    .background(colors.primary),
            ) {
                rail(collapsed) { collapsed = !collapsed }
            }
            Box(modifier = Modifier.weight(1f).fillMaxHeight().imePadding()) {
                content()
            }
        }
    } else {
        // Keyboard terbuka: bilah bawah disembunyikan dan isi naik di atas keyboard.
        val keyboardOpen = WindowInsets.ime.getBottom(LocalDensity.current) > 0

        Column(modifier = modifier.fillMaxSize().background(colors.background)) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .windowInsetsPadding(WindowInsets.statusBars)
                    .imePadding(),
            ) {
                content()
            }
            if (!keyboardOpen) bottomBar()
        }
    }
}
