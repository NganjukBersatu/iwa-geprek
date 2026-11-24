package id.kongstudio.cafe.ui.component.backhandler

import androidx.compose.runtime.Composable

/** Menangkap tombol/gestur kembali sistem selama [enabled]. */
@Composable
expect fun PlatformBackHandler(enabled: Boolean, onBack: () -> Unit)
