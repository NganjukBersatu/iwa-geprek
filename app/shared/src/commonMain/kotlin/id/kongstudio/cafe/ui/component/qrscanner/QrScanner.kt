package id.kongstudio.cafe.ui.component.qrscanner

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.ui.theme.AppTheme

private const val FrameFraction = 0.7f

/** Pratinjau kamera persegi dengan bingkai bidik; [onScanned] menerima isi QR yang terbaca. */
@Composable
fun QrScanner(
    onScanned: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors

    Box(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(1f)
            .clip(AppTheme.shapes.card)
            .background(colors.scrim),
    ) {
        CameraQrPreview(onScanned = onScanned, modifier = Modifier.fillMaxSize())
        Box(
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxSize(FrameFraction)
                .border(AppTheme.sizes.borderThick, colors.accent, AppTheme.shapes.field),
        )
    }
}

/** Pratinjau kamera belakang yang memindai QR; diimplementasikan per platform. */
@Composable
internal expect fun CameraQrPreview(onScanned: (String) -> Unit, modifier: Modifier)
