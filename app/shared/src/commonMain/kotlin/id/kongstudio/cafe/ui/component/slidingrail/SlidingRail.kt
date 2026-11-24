package id.kongstudio.cafe.ui.component.slidingrail

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.Dp
import id.kongstudio.cafe.ui.component.slidingpanel.PanelSide
import id.kongstudio.cafe.ui.component.slidingpanel.SlidingPanel
import id.kongstudio.cafe.ui.theme.AppTheme

/** Rail kiri datar berlatar primary yang meluncur masuk dan keluar sehingga saat tersembunyi [content] memenuhi layar, dengan isi rail dari [rail]. */
@Composable
fun SlidingRail(
    hideDescription: String,
    showDescription: String,
    rail: @Composable ColumnScope.() -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val colors = AppTheme.colors
    var hidden by rememberSaveable { mutableStateOf(false) }
    val verticalBars = WindowInsets.systemBars.only(WindowInsetsSides.Vertical)

    Box(modifier = modifier.fillMaxSize().background(colors.background)) {
        SlidingPanel(
            side = PanelSide.Start,
            hidden = hidden,
            onHiddenChange = { hidden = it },
            panelWidth = AppTheme.sizes.railWidth,
            handleInset = Dp(0f),
            handleDescription = if (hidden) showDescription else hideDescription,
            panel = {
                // Latar mengisi tinggi penuh sampai di bawah bilah sistem; isinya saja yang menghindari bilah itu.
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(colors.primary)
                        .windowInsetsPadding(verticalBars),
                    content = rail,
                )
            },
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .windowInsetsPadding(verticalBars)
                    .imePadding()
                    .padding(start = AppTheme.spacing.xl),
            ) {
                content()
            }
        }
    }
}
