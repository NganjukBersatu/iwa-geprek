package id.kongstudio.cafe.ui.component.donutchart

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import com.patrykandpatrick.vico.compose.common.Fill
import com.patrykandpatrick.vico.compose.common.component.TextComponent
import com.patrykandpatrick.vico.compose.pie.PieChart
import com.patrykandpatrick.vico.compose.pie.PieChartHost
import com.patrykandpatrick.vico.compose.pie.PieSize
import com.patrykandpatrick.vico.compose.pie.data.PieChartModelProducer
import com.patrykandpatrick.vico.compose.pie.data.PieValueFormatter
import com.patrykandpatrick.vico.compose.pie.data.pieModel
import com.patrykandpatrick.vico.compose.pie.rememberPieChart
import id.kongstudio.cafe.ui.component.charttheme.ChartTheme
import id.kongstudio.cafe.ui.component.codebadge.CodeBadge
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlin.math.roundToInt

private val DonutSize = 160.dp
private val DonutHole = 64.dp
private val SliceSpacing = 4.dp

/** Satu irisan donat: [value] menentukan lebarnya dan [color] dipakai juga oleh keterangannya. */
class DonutSlice(val label: String, val value: Long, val color: Color)

/** Grafik donat dari pustaka Vico dengan persentase di tiap irisan dan keterangan nilai di sampingnya. */
@Composable
fun DonutChart(
    slices: List<DonutSlice>,
    valueText: (Long) -> String,
    modifier: Modifier = Modifier,
) {
    val shown = slices.filter { it.value > 0 }
    if (shown.isEmpty()) return
    val colors = AppTheme.colors
    val total = shown.sumOf { it.value }
    val modelProducer = remember { PieChartModelProducer() }
    LaunchedEffect(shown.map { it.value }) {
        modelProducer.runTransaction { pieModel { series(*shown.map { it.value }.toTypedArray()) } }
    }

    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.lg),
    ) {
        ChartTheme {
            PieChartHost(
                chart = rememberPieChart(
                    sliceProvider = PieChart.SliceProvider.series(
                        shown.map { slice ->
                            PieChart.Slice(
                                fill = Fill(slice.color),
                                label = PieChart.SliceLabel.Inside(TextComponent(TextStyle(colors.onPrimary))),
                            )
                        },
                    ),
                    innerSize = PieSize.Inner.fixed(DonutHole),
                    spacing = SliceSpacing,
                    valueFormatter = PieValueFormatter { _, value, _ -> "${(value * 100 / total).roundToInt()}%" },
                ),
                modelProducer = modelProducer,
                modifier = Modifier.size(DonutSize),
            )
        }
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            shown.forEach { slice ->
                CodeBadge(text = "${slice.label}: ${valueText(slice.value)}", color = slice.color)
            }
        }
    }
}
