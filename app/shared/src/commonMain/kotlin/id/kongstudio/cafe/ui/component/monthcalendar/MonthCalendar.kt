package id.kongstudio.cafe.ui.component.monthcalendar

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.monthpicker.MonthPicker
import id.kongstudio.cafe.ui.component.pulsering.pulseRing
import id.kongstudio.cafe.ui.theme.AppTheme

private const val MAX_MARKERS = 3

/** Tiap kotak tanggal mundur setengah spacing.xs dari tepinya, sehingga dua kotak berwarna bersebelahan terpisah celah. */
private const val CellGapDivisor = 2

/** Batas terang warna blok: di bawahnya teks tanggal putih, di atasnya gelap. */
private const val LUMINANCE_SPLIT = 0.5f

/** Kalender satu bulan (minggu mulai Senin) dengan [markers] titik warna, [fills] warna kotak, [pulses] kotak berdenyut, dan [weekdayLabels] berurutan Minggu sampai Sabtu. */
@Composable
internal fun MonthCalendar(
    month: YearMonth,
    monthLabel: String,
    weekdayLabels: List<String>,
    selected: String,
    today: String,
    markers: Map<String, List<Color?>>,
    fills: Map<String, Color>,
    onSelect: (String) -> Unit,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    nextEnabled: Boolean,
    modifier: Modifier = Modifier,
    pulses: Map<String, Color?> = emptyMap(),
    footer: (@Composable ColumnScope.() -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.card
    val leading = (DateTimeFormat.weekdayIndex(DateTimeFormat.firstDay(month)) + 6) % 7
    val cells: List<Int?> = List(leading) { null } + (1..DateTimeFormat.daysInMonth(month)).toList()
    val orderedLabels = weekdayLabels.drop(1) + weekdayLabels.take(1)

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(colors.surface)
            .border(AppTheme.sizes.borderThin, colors.divider, shape)
            .padding(spacing.sm),
        verticalArrangement = Arrangement.spacedBy(spacing.xs),
    ) {
        MonthPicker(
            label = monthLabel,
            onPrevious = onPrevious,
            onNext = onNext,
            nextEnabled = nextEnabled,
        )

        Row(modifier = Modifier.fillMaxWidth()) {
            orderedLabels.forEach { label ->
                BasicText(
                    text = label,
                    style = AppTheme.typography.caption.copy(
                        color = colors.contentMuted,
                        textAlign = TextAlign.Center,
                    ),
                    modifier = Modifier.weight(1f),
                )
            }
        }

        cells.chunked(7).forEach { week ->
            Row(modifier = Modifier.fillMaxWidth()) {
                for (column in 0 until 7) {
                    val day = week.getOrNull(column)
                    if (day == null) {
                        Box(modifier = Modifier.weight(1f).height(AppTheme.spacing.xxxl))
                    } else {
                        val date = DateTimeFormat.dateOf(month, day)
                        DayCell(
                            day = day,
                            isSelected = date == selected,
                            isToday = date == today,
                            markers = markers[date].orEmpty().take(MAX_MARKERS),
                            fill = fills[date],
                            pulse = if (date in pulses) pulses[date] ?: colors.primary else null,
                            onClick = { onSelect(date) },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }

        if (footer != null) {
            AppDivider(modifier = Modifier.padding(vertical = spacing.xs))
            footer()
        }
    }
}

@Composable
private fun DayCell(
    day: Int,
    isSelected: Boolean,
    isToday: Boolean,
    markers: List<Color?>,
    fill: Color?,
    pulse: Color?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field

    Column(
        modifier = modifier
            .height(spacing.xxxl)
            .padding(spacing.xs / CellGapDivisor)
            .clip(shape)
            .pulseRing(active = pulse != null && !isSelected, color = pulse ?: colors.primary, shape = shape)
            .then(
                when {
                    isSelected -> Modifier.background(colors.primary)
                    fill != null -> Modifier.background(fill)
                    else -> Modifier
                },
            )
            .then(
                if (isToday && !isSelected) {
                    Modifier.border(AppTheme.sizes.borderField, colors.primary, shape)
                } else {
                    Modifier
                },
            )
            .clickable(role = Role.Button, onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        BasicText(
            text = day.toString(),
            style = AppTheme.typography.body.copy(
                color = when {
                    isSelected -> colors.onPrimary
                    fill != null -> if (fill.luminance() < LUMINANCE_SPLIT) colors.onPrimary else colors.content
                    else -> colors.content
                },
            ),
        )
        Row(
            modifier = Modifier.height(spacing.md).padding(top = spacing.xs),
            horizontalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            markers.forEach { color ->
                Box(
                    modifier = Modifier
                        .size(spacing.sm)
                        .clip(AppTheme.shapes.pill)
                        .background(color ?: if (isSelected) colors.onPrimary else colors.contentMuted),
                )
            }
        }
    }
}
