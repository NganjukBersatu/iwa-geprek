package id.kongstudio.cafe.ui.component.columnchart

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.patrykandpatrick.vico.compose.cartesian.CartesianChartHost
import com.patrykandpatrick.vico.compose.cartesian.CartesianMeasuringContext
import com.patrykandpatrick.vico.compose.cartesian.axis.Axis
import com.patrykandpatrick.vico.compose.cartesian.axis.HorizontalAxis
import com.patrykandpatrick.vico.compose.cartesian.axis.VerticalAxis
import com.patrykandpatrick.vico.compose.cartesian.data.CartesianChartModelProducer
import com.patrykandpatrick.vico.compose.cartesian.data.CartesianLayerRangeProvider
import com.patrykandpatrick.vico.compose.cartesian.data.CartesianValueFormatter
import com.patrykandpatrick.vico.compose.cartesian.data.ColumnCartesianLayerModel
import com.patrykandpatrick.vico.compose.cartesian.data.columnModel
import com.patrykandpatrick.vico.compose.cartesian.layer.ColumnCartesianLayer
import com.patrykandpatrick.vico.compose.cartesian.layer.rememberColumnCartesianLayer
import com.patrykandpatrick.vico.compose.cartesian.rememberCartesianChart
import com.patrykandpatrick.vico.compose.cartesian.rememberVicoScrollState
import com.patrykandpatrick.vico.compose.cartesian.rememberVicoZoomState
import com.patrykandpatrick.vico.compose.common.Fill
import com.patrykandpatrick.vico.compose.common.component.LineComponent
import com.patrykandpatrick.vico.compose.common.component.TextComponent
import com.patrykandpatrick.vico.compose.common.component.rememberLineComponent
import com.patrykandpatrick.vico.compose.common.data.ExtraStore
import id.kongstudio.cafe.ui.component.charttheme.ChartTheme
import id.kongstudio.cafe.ui.theme.AppTheme

private val ChartHeight = 200.dp
private val ColumnThickness = 20.dp
/** Lebar jatah satu kolom dan lebar terkecil grafik, supaya satu atau dua kolom tidak melebar selebar seluruh grafik. */
private val ColumnSlot = 96.dp
private val MinChartWidth = 200.dp

/**
 * Grafik kolom dari pustaka Vico: satu kolom per nilai, [labels] di sumbu bawah dan [axisText] di sumbu kiri.
 * [colors] memberi tiap kolom warnanya sendiri (berulang bila kurang), dan [valueText] menuliskan nilai di atas tiap kolom.
 */
@Composable
fun ColumnChart(
    values: List<Long>,
    labels: List<String>,
    axisText: (Long) -> String,
    modifier: Modifier = Modifier,
    colors: List<Color> = emptyList(),
    valueText: ((Long) -> String)? = null,
) {
    if (values.isEmpty()) return
    val modelProducer = remember { CartesianChartModelProducer() }
    LaunchedEffect(values) {
        modelProducer.runTransaction { columnModel { series(values.indices.toList(), values) } }
    }
    val bottomFormatter = remember(labels) { labelFormatter { value -> labels.getOrNull(value.toInt()).orEmpty() } }
    val startFormatter = remember(axisText) { labelFormatter { value -> axisText(value.toLong()) } }
    val dataFormatter = remember(valueText) { valueText?.let { text -> labelFormatter { value -> text(value.toLong()) } } }

    val fills = colors.ifEmpty { listOf(AppTheme.colors.primary) }
    val columns = fills.map { rememberLineComponent(fill = Fill(it), thickness = ColumnThickness) }
    val provider = remember(columns) { PerColumn(columns) }
    val dataLabel = valueText?.let { TextComponent(TextStyle(color = AppTheme.colors.content, fontWeight = FontWeight.SemiBold)) }

    ChartTheme {
        CartesianChartHost(
            chart = rememberCartesianChart(
                if (dataFormatter != null && dataLabel != null) {
                    rememberColumnCartesianLayer(
                        columnProvider = provider,
                        dataLabel = dataLabel,
                        dataLabelValueFormatter = dataFormatter,
                        rangeProvider = remember(values) { CartesianLayerRangeProvider.fixed(minY = 0.0, maxY = roomyMax(values)) },
                    )
                } else {
                    rememberColumnCartesianLayer(columnProvider = provider)
                },
                startAxis = VerticalAxis.rememberStart(valueFormatter = startFormatter),
                bottomAxis = HorizontalAxis.rememberBottom(
                    itemPlacer = remember { HorizontalAxis.ItemPlacer.segmented() },
                    valueFormatter = bottomFormatter,
                ),
            ),
            modelProducer = modelProducer,
            modifier = modifier.widthIn(max = maxOf(MinChartWidth, ColumnSlot * values.size)).fillMaxWidth().height(ChartHeight),
            scrollState = rememberVicoScrollState(scrollEnabled = false),
            zoomState = rememberVicoZoomState(zoomEnabled = false),
        )
    }
}

/** Puncak sumbu sekitar 20% di atas kolom tertinggi, dibulatkan ke angka rapi, supaya label nilainya tidak terpotong. */
private fun roomyMax(values: List<Long>): Double {
    val target = (values.maxOrNull() ?: 0L).coerceAtLeast(1L) * 1.2
    var step = 1.0
    while (step * 10 <= target) step *= 10
    val half = step / 2
    return kotlin.math.ceil(target / half) * half
}

private fun labelFormatter(text: (Double) -> String) = object : CartesianValueFormatter {
    override fun format(context: CartesianMeasuringContext, value: Double, verticalAxisPosition: Axis.Position.Vertical?) = text(value)
}

/** Warna dipilih per posisi kolom, bukan per seri, karena grafik ini hanya punya satu seri. */
@Immutable
private data class PerColumn(private val columns: List<LineComponent>) : ColumnCartesianLayer.ColumnProvider {
    override fun getColumn(entry: ColumnCartesianLayerModel.Entry, extraStore: ExtraStore): LineComponent =
        columns[entry.x.toInt().mod(columns.size)]

    override fun getWidestSeriesColumn(seriesKey: Any, seriesIndex: Int, extraStore: ExtraStore): LineComponent = columns.first()
}
