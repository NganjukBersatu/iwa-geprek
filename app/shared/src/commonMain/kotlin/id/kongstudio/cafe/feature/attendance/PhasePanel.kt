package id.kongstudio.cafe.feature.attendance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.dayplan.DaySegment
import id.kongstudio.cafe.feature.dayplan.SegmentKind
import id.kongstudio.cafe.feature.dayplan.activeSegment
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_time_range
import id.kongstudio.cafe.resources.phase_duration
import id.kongstudio.cafe.resources.phase_duration_remaining
import id.kongstudio.cafe.resources.phase_filter_all
import id.kongstudio.cafe.resources.phase_filter_overtime
import id.kongstudio.cafe.resources.phase_filter_work
import id.kongstudio.cafe.resources.phase_hint
import id.kongstudio.cafe.resources.phase_none
import id.kongstudio.cafe.resources.phase_overtime
import id.kongstudio.cafe.resources.phase_overtime_unplanned
import id.kongstudio.cafe.resources.phase_title
import id.kongstudio.cafe.resources.phase_work
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.segmentbar.BarSegment
import id.kongstudio.cafe.ui.component.segmentbar.BarTone
import id.kongstudio.cafe.ui.component.segmentbar.SegmentBar
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.delay
import org.jetbrains.compose.resources.stringResource

private const val TickMillis = 1_000L
private const val SecondsPerMinute = 60L

/** Rentang jam yang ditampilkan: hanya kerja, semuanya, atau hanya lembur. */
private enum class PhaseFilter { Work, All, Overtime }

/** Bilah seluruh rentang hari ini dengan rincian rentang yang aktif atau yang diketuk di bawahnya. */
@Composable
internal fun PhasePanel(
    segments: List<DaySegment>,
    clockedIn: Boolean,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    var now by remember { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(TickMillis)
            now = ServerClock.nowEpochSeconds()
        }
    }
    var filter by rememberSaveable { mutableStateOf(PhaseFilter.All) }
    var selectedIndex by remember(segments, filter) { mutableStateOf<Int?>(null) }

    val visible = when (filter) {
        PhaseFilter.Work -> segments.filter { !it.isOvertime }
        PhaseFilter.All -> segments
        PhaseFilter.Overtime -> segments.filter { it.isOvertime }
    }
    val active = activeSegment(segments, now, clockedIn)
    val shown = selectedIndex?.let(visible::getOrNull) ?: active?.takeIf { it in visible }

    ListCard(modifier = modifier) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(spacing.md),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            // Satu baris tiga pilihan sama lebar: label panjang membungkus di dalam pilihannya, tidak menjatuhkan satu pilihan ke baris sendiri.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                listOf(
                    PhaseFilter.Work to stringResource(Res.string.phase_filter_work),
                    PhaseFilter.All to stringResource(Res.string.phase_filter_all),
                    PhaseFilter.Overtime to stringResource(Res.string.phase_filter_overtime),
                ).forEach { (option, label) ->
                    AppChip(label = label, selected = filter == option, onClick = { filter = option }, modifier = Modifier.weight(1f))
                }
            }

            if (visible.isNotEmpty()) {
                SegmentBar(
                    segments = visible.map { segment ->
                        BarSegment(
                            weight = segment.minutes.toFloat(),
                            progress = (now - segment.startEpoch).toFloat() / (segment.endEpoch - segment.startEpoch),
                            tone = if (segment.isOvertime) BarTone.Accent else BarTone.Primary,
                        )
                    },
                    onSelect = { selectedIndex = if (selectedIndex == it) null else it },
                )
            }

            PhaseSummary(segment = shown, isActive = shown != null && shown === active, now = now)
        }
    }
}

@Composable
private fun PhaseSummary(segment: DaySegment?, isActive: Boolean, now: Long) {
    val title = segment?.let {
        stringResource(
            Res.string.phase_title,
            phaseLabel(it.kind),
            stringResource(Res.string.format_time_range, it.start.time, it.end.time),
        )
    } ?: stringResource(Res.string.phase_none)
    val detail = when {
        segment == null -> stringResource(Res.string.phase_hint)
        isActive -> {
            val left = ((segment.endEpoch - now) / SecondsPerMinute).toInt().coerceAtLeast(0)
            stringResource(Res.string.phase_duration_remaining, durationLabel(segment.minutes), durationLabel(left))
        }
        else -> stringResource(Res.string.phase_duration, durationLabel(segment.minutes))
    }

    AppText(text = title, role = TextRole.Title, textAlign = TextAlign.Center)
    AppText(text = detail, role = TextRole.Caption, color = AppTheme.colors.contentMuted, textAlign = TextAlign.Center)
}

@Composable
private fun phaseLabel(kind: SegmentKind): String = stringResource(
    when (kind) {
        SegmentKind.Work -> Res.string.phase_work
        SegmentKind.ScheduledOvertime -> Res.string.phase_overtime
        SegmentKind.UnplannedOvertime -> Res.string.phase_overtime_unplanned
    },
)
