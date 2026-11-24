package id.kongstudio.cafe.feature.network

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.delay

/** Putus yang lebih singkat dari ini tidak memunculkan halaman, agar pindah jaringan tidak membuat layar berkedip. */
private const val GraceMillis = 1500L

/** Menutupi [content] dengan [NoConnectionScreen] selama internet putus tanpa membongkar [content], sehingga halaman dan isian yang terbuka tidak hilang. */
@Composable
fun NetworkGate(
    monitor: NetworkMonitor,
    modifier: Modifier = Modifier,
    /** False untuk halaman yang tetap berguna tanpa internet, sehingga tidak ditutup oleh [NoConnectionScreen]. */
    blocking: Boolean = true,
    content: @Composable () -> Unit,
) {
    val effects = AppTheme.effects
    val online by monitor.online.collectAsState()
    var lost by remember { mutableStateOf(false) }

    LaunchedEffect(online) {
        if (online) {
            lost = false
        } else {
            delay(GraceMillis)
            lost = true
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        content()
        AnimatedVisibility(
            visible = lost && blocking,
            enter = fadeIn(tween(effects.standardMillis)),
            exit = fadeOut(tween(effects.standardMillis)),
        ) {
            NoConnectionScreen()
        }
    }
}
