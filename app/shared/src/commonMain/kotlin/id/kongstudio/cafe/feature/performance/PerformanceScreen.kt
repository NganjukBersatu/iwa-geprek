package id.kongstudio.cafe.feature.performance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.performance_composition_title
import id.kongstudio.cafe.resources.performance_counted
import id.kongstudio.cafe.resources.performance_empty
import id.kongstudio.cafe.resources.performance_hours_caption
import id.kongstudio.cafe.resources.performance_hours_title
import id.kongstudio.cafe.resources.performance_ontime_caption
import id.kongstudio.cafe.resources.performance_ontime_title
import id.kongstudio.cafe.resources.performance_period
import id.kongstudio.cafe.resources.performance_range_all
import id.kongstudio.cafe.resources.performance_range_cycle
import id.kongstudio.cafe.resources.performance_range_previous
import id.kongstudio.cafe.resources.performance_rating_close
import id.kongstudio.cafe.resources.performance_rating_none
import id.kongstudio.cafe.resources.performance_rating_open
import id.kongstudio.cafe.resources.performance_rating_stars_description
import id.kongstudio.cafe.resources.performance_rating_title
import id.kongstudio.cafe.resources.performance_rating_value
import id.kongstudio.cafe.resources.performance_slice_absent
import id.kongstudio.cafe.resources.performance_slice_late
import id.kongstudio.cafe.resources.performance_slice_leave
import id.kongstudio.cafe.resources.performance_slice_on_time
import id.kongstudio.cafe.resources.performance_tasks_caption
import id.kongstudio.cafe.resources.performance_tasks_title
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.columnchart.ColumnChart
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.donutchart.DonutChart
import id.kongstudio.cafe.ui.component.donutchart.DonutSlice
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.ratingcard.RatingCard
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.segmentedcontrol.SegmentedControl
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val MinutesPerHour = 60

private fun bucketLabel(date: String) = "${DateTimeFormat.dayOfMonth(date)}/${DateTimeFormat.monthIndex(date) + 1}"

/** Halaman Kinerja: pilihan rentang, tanggal rentang, lalu grafik; setiap angka hanya tampil satu kali. */
@Composable
internal fun PerformanceScreen(
    state: PerformanceUiState,
    onSelectRange: (PerformanceRange) -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val ranges = PerformanceRange.entries
    val labels = listOf(
        stringResource(Res.string.performance_range_cycle),
        stringResource(Res.string.performance_range_previous),
        stringResource(Res.string.performance_range_all),
    )
    val failure = state.failure
    val performance = state.performance

    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = AppTheme.windowSize.pagePadding),
        contentAlignment = Alignment.TopCenter,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .verticalScroll(rememberScrollState())
                .padding(bottom = spacing.xl),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            SegmentedControl(
                options = labels,
                selectedIndex = ranges.indexOf(state.range),
                onSelect = { onSelectRange(ranges[it]) },
            )
            when {
                failure != null -> ListCard { FailureState(failure = failure, onRetry = onRetry) }
                state.loading || performance == null -> LoadingState()
                else -> Charts(performance)
            }
        }
    }
}

@Composable
private fun Charts(performance: Performance) {
    val colors = AppTheme.colors
    val labels = performance.buckets.map { bucketLabel(it.start) }
    val composition = performance.composition

    AppText(
        text = stringResource(
            Res.string.performance_period,
            longDateLabel(performance.start),
            longDateLabel(performance.end),
        ),
        role = TextRole.Label,
        color = colors.content,
    )
    AppText(
        text = stringResource(Res.string.performance_counted, performance.countedDays.toString()),
        role = TextRole.Caption,
        color = colors.contentMuted,
    )

    if (performance.countedDays == 0) {
        AppText(text = stringResource(Res.string.performance_empty), role = TextRole.Body, color = colors.contentMuted)
        return
    }

    val rating = performance.rating
    val stars = rating.stars
    Column {
        SectionTitle(
            stringResource(Res.string.performance_rating_title),
            padded = false,
            modifier = Modifier.padding(bottom = AppTheme.spacing.sm),
        )
        RatingCard(
            stars = stars?.toFloat() ?: 0f,
            valueText = if (stars == null) {
                stringResource(Res.string.performance_rating_none)
            } else {
                stringResource(Res.string.performance_rating_value, stars.starsText())
            },
            starsDescription = stringResource(Res.string.performance_rating_stars_description, (stars ?: 0.0).starsText()),
            openLabel = stringResource(Res.string.performance_rating_open),
            closeLabel = stringResource(Res.string.performance_rating_close),
            details = if (stars == null) {
                null
            } else {
                {
                    rating.groups.forEachIndexed { index, group ->
                        if (index > 0) AppDivider()
                        SectionTitle(
                            group.label(),
                            padded = false,
                            modifier = Modifier.padding(start = AppTheme.spacing.md, top = AppTheme.spacing.md),
                        )
                        group.components.forEach { DetailRow(it.label(), value = it.valueText()) }
                    }
                }
            },
        )
    }

    ChartCard(
        title = stringResource(Res.string.performance_ontime_title),
        caption = stringResource(Res.string.performance_ontime_caption),
    ) {
        ColumnChart(
            values = performance.buckets.map { (it.onTimePercent ?: 0).toLong() },
            labels = labels,
            axisText = { "$it%" },
        )
    }

    ChartCard(title = stringResource(Res.string.performance_composition_title), caption = null) {
        DonutChart(
            slices = listOf(
                DonutSlice(stringResource(Res.string.performance_slice_on_time), composition.onTime.toLong(), colors.success),
                DonutSlice(stringResource(Res.string.performance_slice_late), composition.late.toLong(), colors.warning),
                DonutSlice(stringResource(Res.string.performance_slice_leave), composition.leave.toLong(), colors.info),
                DonutSlice(stringResource(Res.string.performance_slice_absent), composition.absent.toLong(), colors.danger),
            ),
            valueText = { it.toString() },
        )
    }

    ChartCard(
        title = stringResource(Res.string.performance_hours_title),
        caption = stringResource(
            Res.string.performance_hours_caption,
            durationLabel(performance.workMinutes),
            durationLabel(performance.overtimeMinutes),
        ),
    ) {
        ColumnChart(
            values = performance.buckets.map { (it.workMinutes / MinutesPerHour).toLong() },
            labels = labels,
            axisText = { "$it" },
        )
    }

    ChartCard(
        title = stringResource(Res.string.performance_tasks_title),
        caption = stringResource(
            Res.string.performance_tasks_caption,
            performance.tasksDone.toString(),
            performance.tasksAssigned.toString(),
        ),
    ) {
        ColumnChart(
            values = performance.buckets.map { it.tasksDone.toLong() },
            labels = labels,
            axisText = { "$it" },
        )
    }
}

/** Satu grafik dalam kartu: judul di atas kartu, keterangan angka di dalamnya. */
@Composable
private fun ChartCard(
    title: String,
    caption: String?,
    chart: @Composable () -> Unit,
) {
    val spacing = AppTheme.spacing

    Column {
        SectionTitle(title, padded = false, modifier = Modifier.padding(bottom = spacing.sm))
        ListCard {
            Column(
                modifier = Modifier.padding(spacing.md),
                verticalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                if (caption != null) {
                    AppText(text = caption, role = TextRole.Caption, color = AppTheme.colors.contentMuted)
                }
                chart()
            }
        }
    }
}
