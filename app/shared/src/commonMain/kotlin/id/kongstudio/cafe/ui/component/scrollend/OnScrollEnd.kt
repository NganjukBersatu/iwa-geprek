package id.kongstudio.cafe.ui.component.scrollend

import androidx.compose.foundation.ScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.platform.LocalDensity
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filter

private const val RowsBeforeEnd = 3

/** Memanggil [onEnd] saat [scroll] mendekati ujung bawah, termasuk saat isinya belum cukup panjang untuk digulir; [count] dipakai supaya pemeriksaan diulang setiap isi bertambah. */
@Composable
internal fun OnScrollEnd(scroll: ScrollState, count: Int, onEnd: () -> Unit) {
    val margin = with(LocalDensity.current) { AppTheme.spacing.touchTarget.toPx() } * RowsBeforeEnd
    LaunchedEffect(scroll, count) {
        snapshotFlow { scroll.value >= scroll.maxValue - margin }
            .distinctUntilChanged()
            .filter { it }
            .collect { onEnd() }
    }
}
