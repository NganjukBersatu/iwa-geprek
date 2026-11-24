package id.kongstudio.cafe.feature.attendance

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.durationLabel
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_done_action
import id.kongstudio.cafe.resources.attendance_done_in_message
import id.kongstudio.cafe.resources.attendance_done_in_title
import id.kongstudio.cafe.resources.attendance_done_out_message
import id.kongstudio.cafe.resources.attendance_done_out_title
import id.kongstudio.cafe.ui.component.successtakeover.SuccessTakeover
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Perayaan absen: warna teks untuk datang dan warna aksen untuk pulang, sewarna dengan tombol absennya. */
@Composable
internal fun ClockCelebrationOverlay(celebration: ClockCelebration, onDone: () -> Unit) {
    val colors = AppTheme.colors
    val isIn = celebration.kind == ClockKind.In

    SuccessTakeover(
        title = stringResource(if (isIn) Res.string.attendance_done_in_title else Res.string.attendance_done_out_title),
        message = stringResource(if (isIn) Res.string.attendance_done_in_message else Res.string.attendance_done_out_message),
        countTo = celebration.minutes,
        countLabel = { minutes -> if (isIn) DateTimeFormat.clockOf(minutes) else durationLabel(minutes) },
        actionLabel = stringResource(Res.string.attendance_done_action),
        containerColor = if (isIn) colors.primary else colors.accent,
        contentColor = if (isIn) colors.onPrimary else colors.content,
        onDone = onDone,
    )
}
