package id.kongstudio.cafe.ui.component.loadable

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.togetherWith
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.TimeSource
import kotlinx.coroutines.delay

private const val MinShownMillis = 350
private const val EnterMillis = 280
private const val ExitMillis = 140
private const val SlideDivisor = 28

/** Bentuk kerangka yang ditampilkan selama memuat; dipilih agar mirip isi yang akan datang. */
enum class LoadingVariant {
    /** Deretan baris, untuk daftar. */
    List,

    /** Kisi kartu, untuk menu atau pesanan. */
    Cards,

    /** Kolom-kolom berisi kartu, untuk papan. */
    Board,

    /** Judul dan beberapa baris, untuk rincian satu data. */
    Detail,
}

/** Satu-satunya pintu keadaan memuat: kerangka berkilau sampai [content] siap (minimal sebentar agar tidak berkedip), lalu perpindahan halus. */
@Composable
fun Loadable(
    loading: Boolean,
    modifier: Modifier = Modifier,
    variant: LoadingVariant = LoadingVariant.List,
    rows: Int = DefaultSkeletonRows,
    content: @Composable () -> Unit,
) {
    var showingSkeleton by remember { mutableStateOf(loading) }
    var shownSince by remember { mutableStateOf(TimeSource.Monotonic.markNow()) }

    LaunchedEffect(loading) {
        if (loading) {
            if (!showingSkeleton) shownSince = TimeSource.Monotonic.markNow()
            showingSkeleton = true
        } else if (showingSkeleton) {
            val remaining = MinShownMillis.milliseconds - shownSince.elapsedNow()
            if (remaining.isPositive()) delay(remaining)
            showingSkeleton = false
        }
    }

    AnimatedContent(
        targetState = showingSkeleton,
        modifier = modifier,
        transitionSpec = {
            (fadeIn(tween(EnterMillis)) + slideInVertically(tween(EnterMillis)) { it / SlideDivisor }) togetherWith
                fadeOut(tween(ExitMillis))
        },
        label = "loadable",
    ) { skeleton ->
        if (skeleton) LoadingSkeleton(variant = variant, rows = rows) else content()
    }
}

internal const val DefaultSkeletonRows = 4
