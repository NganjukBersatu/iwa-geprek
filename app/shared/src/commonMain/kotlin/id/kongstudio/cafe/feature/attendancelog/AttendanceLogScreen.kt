package id.kongstudio.cafe.feature.attendancelog

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.resources.dashboard_empty_attendance
import id.kongstudio.cafe.resources.dashboard_hero_empty
import id.kongstudio.cafe.resources.dashboard_hero_label
import id.kongstudio.cafe.resources.dashboard_hero_sub
import id.kongstudio.cafe.resources.dashboard_hero_value
import id.kongstudio.cafe.resources.dashboard_section_attendance
import id.kongstudio.cafe.resources.dashboard_stat_late
import id.kongstudio.cafe.resources.dashboard_stat_not_present
import id.kongstudio.cafe.resources.dashboard_stat_penalty
import id.kongstudio.cafe.resources.dashboard_stat_present
import id.kongstudio.cafe.resources.format_month_year
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.weekdays_short
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.datebadge.DateBadge
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.monthpicker.MonthPicker
import id.kongstudio.cafe.ui.component.progressring.ProgressRing
import id.kongstudio.cafe.ui.component.statcard.StatCard
import id.kongstudio.cafe.ui.component.statelistcard.StateListCard
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlin.math.roundToInt
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

private const val SkeletonRows = 4
private const val PercentFull = 100

/** Halaman Kehadiran: ringkasan bulan, hitungan, potongan, dan hari-hari absen; judul dan tombol kembali dari halaman induk. */
@Composable
internal fun AttendanceLogScreen(
    state: AttendanceLogUiState,
    onPreviousMonth: () -> Unit,
    onNextMonth: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val attendance = state.attendance
    val failure = state.failure
    val months = stringArrayResource(Res.array.months)
    var selectedDay by remember { mutableStateOf<AttendanceDay?>(null) }

    selectedDay?.let { day -> AttendanceDetailSheet(day = day, onDismiss = { selectedDay = null }) }

    val monthLabel = state.month?.let {
        stringResource(Res.string.format_month_year, months[it.month - 1], it.year.toString())
    }.orEmpty()
    val total = attendance?.let { it.present + it.notPresent } ?: 0
    val progress = if (attendance != null && total > 0) attendance.present.toFloat() / total else 0f
    val heroSub = when {
        failure != null -> failureText(failure)
        attendance == null -> stringResource(Res.string.common_loading)
        else -> stringResource(Res.string.dashboard_hero_sub, attendance.late.toString(), attendance.notPresent.toString())
    }
    val heroLabel = state.month?.let {
        stringResource(Res.string.dashboard_hero_label, months[it.month - 1], it.year.toString())
    } ?: stringResource(Res.string.dashboard_section_attendance)
    val heroValue = if (attendance == null) {
        stringResource(Res.string.dashboard_hero_empty)
    } else {
        stringResource(Res.string.dashboard_hero_value, attendance.present.toString(), total.toString())
    }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        Column(
            modifier = Modifier
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = AppTheme.windowSize.pagePadding)
                .padding(bottom = AppTheme.spacing.xl),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
        ) {
            Summary(progress = progress, label = heroLabel, value = heroValue, sub = heroSub)
            MonthPicker(
                label = monthLabel,
                onPrevious = onPreviousMonth,
                onNext = onNextMonth,
                nextEnabled = state.canGoNext && !state.loading,
            )
            if (failure != null) {
                ListCard { FailureState(failure = failure, onRetry = onRetry) }
            } else {
                if (attendance != null && attendance.days.isNotEmpty() && !state.loading) {
                    Tally(attendance)
                    StatCard(
                        label = stringResource(Res.string.dashboard_stat_penalty),
                        value = formatRupiah(attendance.penalty),
                        valueColor = if (attendance.penalty > 0) colors.danger else colors.content,
                        icon = AppIcons.Alert,
                        iconBeside = true,
                    )
                }
                StateListCard(
                    loading = state.loading,
                    empty = attendance == null || attendance.days.isEmpty(),
                    emptyText = stringResource(Res.string.dashboard_empty_attendance),
                    skeletonRows = SkeletonRows,
                ) {
                    DividedItems(attendance?.days.orEmpty()) { day -> DayRow(day, onClick = { selectedDay = day }) }
                }
            }
        }
    }
}

/** Kartu ringkasan bulan: cincin persen di kiri, label, nilai, dan keterangan di kanan. */
@Composable
private fun Summary(progress: Float, label: String, value: String, sub: String) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(AppTheme.shapes.card)
            .background(colors.primary)
            .padding(spacing.lg),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.lg),
    ) {
        ProgressRing(
            progress = progress,
            label = "${(progress * PercentFull).roundToInt()}%",
            trackColor = colors.onPrimarySubtle,
            indicatorColor = colors.accent,
            labelColor = colors.onPrimary,
        )
        Column(modifier = Modifier.weight(1f)) {
            AppText(text = label, role = TextRole.Caption, color = colors.onPrimaryMuted)
            AppText(text = value, role = TextRole.Title, color = colors.onPrimary)
            AppText(text = sub, role = TextRole.Caption, color = colors.onPrimaryMuted)
        }
    }
}

/** Tiga hitungan kehadiran: hadir, telat, dan tidak hadir. */
@Composable
private fun Tally(attendance: AttendanceMonth) {
    Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        StatCard(stringResource(Res.string.dashboard_stat_present), attendance.present.toString(), Modifier.weight(1f))
        StatCard(stringResource(Res.string.dashboard_stat_late), attendance.late.toString(), Modifier.weight(1f))
        StatCard(
            stringResource(Res.string.dashboard_stat_not_present),
            attendance.notPresent.toString(),
            Modifier.weight(1f),
        )
    }
}

@Composable
private fun DayRow(day: AttendanceDay, onClick: () -> Unit) {
    val weekdays = stringArrayResource(Res.array.weekdays_short)
    val clockIn = DateTimeFormat.clock(day.clockIn)
    val clockOut = DateTimeFormat.clock(day.clockOut)
    val time = when {
        clockIn == null -> "—"
        clockOut == null -> "$clockIn –"
        else -> "$clockIn – $clockOut"
    }
    ListRow(
        title = time,
        onClick = onClick,
        leading = {
            DateBadge(
                weekday = weekdays[DateTimeFormat.weekdayIndex(day.date)],
                day = DateTimeFormat.dayOfMonth(day.date),
            )
        },
        trailing = { AttendanceStatusBadge(day) },
    )
}
