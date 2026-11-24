package id.kongstudio.cafe.feature.schedule

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_date_long
import id.kongstudio.cafe.resources.format_month_year
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.schedule_codes
import id.kongstudio.cafe.resources.schedule_day_off
import id.kongstudio.cafe.resources.schedule_empty
import id.kongstudio.cafe.resources.schedule_only_mine
import id.kongstudio.cafe.resources.schedule_outlet
import id.kongstudio.cafe.resources.schedule_overtime
import id.kongstudio.cafe.resources.weekdays_long
import id.kongstudio.cafe.resources.weekdays_short
import id.kongstudio.cafe.ui.component.codelegend.CodeLegendItem
import id.kongstudio.cafe.ui.component.codelegendtrigger.CodeLegendTrigger
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.monthcalendar.MonthCalendar
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.color.parseHexColor
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun ScheduleScreen(
    state: ScheduleUiState,
    onSelect: (String) -> Unit,
    onToggleOnlyMine: () -> Unit,
    onPreviousMonth: () -> Unit,
    onNextMonth: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val months = stringArrayResource(Res.array.months)
    val weekdaysShort = stringArrayResource(Res.array.weekdays_short)
    val weekdaysLong = stringArrayResource(Res.array.weekdays_long)
    val selected = state.selected
    val dayOff = stringResource(Res.string.schedule_day_off)
    val legend = state.codes.map { code ->
        val hours = if (code.off || code.start == null || code.end == null) {
            dayOff
        } else {
            stringResource(Res.string.format_time_range, code.start, code.end)
        }
        val overtime = if (code.overtimeStart != null && code.overtimeEnd != null) {
            stringResource(
                Res.string.schedule_overtime,
                stringResource(Res.string.format_time_range, code.overtimeStart, code.overtimeEnd),
            )
        } else {
            null
        }
        CodeLegendItem(
            code = code.code,
            color = parseHexColor(code.color),
            title = code.category ?: hours,
            detail = if (code.category != null) hours else null,
            caption = overtime,
        )
    }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight(),
            contentPadding = PaddingValues(
                horizontal = AppTheme.windowSize.pagePadding,
                vertical = spacing.lg,
            ),
            verticalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    state.outletName?.let { name ->
                        SectionTitle(
                            text = stringResource(Res.string.schedule_outlet, name),
                            padded = false,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    ToggleSwitch(
                        label = stringResource(Res.string.schedule_only_mine),
                        checked = state.onlyMine,
                        onCheckedChange = { onToggleOnlyMine() },
                    )
                }
            }

            item {
                MonthCalendar(
                    month = state.month,
                    monthLabel = stringResource(
                        Res.string.format_month_year,
                        months[state.month.month - 1],
                        state.month.year.toString(),
                    ),
                    weekdayLabels = weekdaysShort,
                    selected = selected,
                    today = state.today,
                    markers = state.markers,
                    fills = state.fills,
                    pulses = state.pulses,
                    onSelect = onSelect,
                    onPrevious = onPreviousMonth,
                    onNext = onNextMonth,
                    nextEnabled = state.canGoNext && !state.loading,
                    footer = if (legend.isEmpty()) {
                        null
                    } else {
                        { CodeLegendTrigger(title = stringResource(Res.string.schedule_codes), items = legend) }
                    },
                )
            }

            item {
                SectionTitle(
                    stringResource(
                        Res.string.format_date_long,
                        weekdaysLong[DateTimeFormat.weekdayIndex(selected)],
                        DateTimeFormat.dayOfMonth(selected),
                        months[DateTimeFormat.monthIndex(selected)],
                        selected.take(4),
                    ),
                )
            }

            if (state.failure != null) {
                item { FailureState(failure = state.failure!!, onRetry = onRetry) }
            } else {
                item {
                    StateListCard(
                        loading = state.loading,
                        empty = state.dayItems.isEmpty(),
                        emptyText = stringResource(Res.string.schedule_empty),
                    ) {
                        DividedItems(state.dayItems) { entry -> ScheduleRow(item = entry, showUser = true) }
                    }
                }
            }
        }
    }
}
