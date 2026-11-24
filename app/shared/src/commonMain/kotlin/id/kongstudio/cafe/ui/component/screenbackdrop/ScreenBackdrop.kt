package id.kongstudio.cafe.ui.component.screenbackdrop

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme

/** Latar layar penuh berwarna dasar yang menghindari bilah sistem, untuk layar di luar kerangka aplikasi. */
@Composable
fun ScreenBackdrop(
    modifier: Modifier = Modifier,
    contentAlignment: Alignment = Alignment.TopStart,
    content: @Composable BoxScope.() -> Unit,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AppTheme.colors.background)
            .safeDrawingPadding(),
        contentAlignment = contentAlignment,
        content = content,
    )
}
