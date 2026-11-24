package id.kongstudio.cafe.ui.component.charttheme

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import com.patrykandpatrick.vico.compose.common.ProvideVicoTheme
import com.patrykandpatrick.vico.compose.common.vicoTheme
import id.kongstudio.cafe.ui.theme.AppTheme

/** Membuat grafik Vico memakai warna aplikasi, bukan warna bawaan yang mengikuti mode gelap ponsel. */
@Composable
fun ChartTheme(content: @Composable () -> Unit) {
    val colors = AppTheme.colors
    val base = vicoTheme
    val theme = remember(base, colors) {
        base.copy(
            columnCartesianLayerColors = listOf(colors.primary, colors.accent),
            pieChartColors = listOf(colors.primary, colors.accent),
            lineColor = colors.divider,
            textColor = colors.content,
        )
    }
    ProvideVicoTheme(theme, content)
}
