package id.kongstudio.cafe.feature.attendance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_action_in
import id.kongstudio.cafe.resources.attendance_action_out
import id.kongstudio.cafe.resources.attendance_distance_inside
import id.kongstudio.cafe.resources.attendance_distance_locating
import id.kongstudio.cafe.resources.attendance_distance_outside
import id.kongstudio.cafe.resources.attendance_distance_refresh
import id.kongstudio.cafe.resources.attendance_location_unavailable
import id.kongstudio.cafe.resources.attendance_outside_note
import id.kongstudio.cafe.resources.attendance_outside_toggle
import id.kongstudio.cafe.resources.attendance_submit
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.photosubmitform.PhotoSubmitForm
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlin.math.roundToInt
import org.jetbrains.compose.resources.stringResource

/** Lembar absen: foto dari kamera, dan keterangan wajib bila absen dilakukan di luar lokasi cabang. */
@Composable
internal fun ClockSheet(
    kind: ClockKind,
    submitting: Boolean,
    submitError: UiText?,
    onSubmit: (photo: ByteArray, outside: Boolean, note: String) -> Unit,
    onDismiss: () -> Unit,
    notice: String? = null,
    branch: AttendanceBranch? = null,
    distance: Double? = null,
    locating: Boolean = false,
    located: Boolean = false,
    onRelocate: () -> Unit = {},
) {
    var outside by remember { mutableStateOf(false) }
    var note by remember { mutableStateOf("") }
    val title = stringResource(if (kind == ClockKind.In) Res.string.attendance_action_in else Res.string.attendance_action_out)
    val radius = branch?.radiusMeters
    // Sama dengan aturan server: absen di lokasi ditolak bila jaraknya melewati radius.
    val beyondRadius = distance != null && radius != null && distance > radius

    AppBottomSheet(title = title, onDismiss = onDismiss) {
        notice?.let { Notice(it, modifier = Modifier.padding(bottom = AppTheme.spacing.md)) }
        DistanceNotice(branch, distance, beyondRadius && !outside, locating, located, onRelocate)
        PhotoSubmitForm(
            submitLabel = stringResource(Res.string.attendance_submit),
            onSubmit = { photo -> if (photo != null) onSubmit(photo, outside, note) },
            submitting = submitting,
            canSubmit = if (outside) note.isNotBlank() else !beyondRadius,
            allowGallery = false,
            error = submitError?.resolve(),
        ) {
            ToggleSwitch(
                label = stringResource(Res.string.attendance_outside_toggle),
                checked = outside,
                onCheckedChange = { outside = it },
            )
            if (outside) {
                AppTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = stringResource(Res.string.attendance_outside_note),
                    enabled = !submitting,
                )
            }
        }
    }
}

/** Jarak ke cabang sebelum memotret, seperti di PWA; tidak tampil bila cabang tanpa titik atau radius. */
@Composable
private fun DistanceNotice(
    branch: AttendanceBranch?,
    distance: Double?,
    blocking: Boolean,
    locating: Boolean,
    located: Boolean,
    onRelocate: () -> Unit,
) {
    val radius = branch?.radiusMeters ?: return
    if (branch.latitude == null || branch.longitude == null) return
    val text = when {
        locating -> stringResource(Res.string.attendance_distance_locating)
        distance == null && located -> stringResource(Res.string.attendance_location_unavailable)
        distance == null -> return
        blocking -> stringResource(
            Res.string.attendance_distance_outside,
            distance.roundToInt().toString(),
            branch.name,
            radius.toString(),
        )
        else -> stringResource(
            Res.string.attendance_distance_inside,
            distance.roundToInt().toString(),
            branch.name,
            radius.toString(),
        )
    }
    Column(
        modifier = Modifier.padding(bottom = AppTheme.spacing.md),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        Notice(text)
        if (!locating) {
            SecondaryButton(
                text = stringResource(Res.string.attendance_distance_refresh),
                onClick = onRelocate,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}
