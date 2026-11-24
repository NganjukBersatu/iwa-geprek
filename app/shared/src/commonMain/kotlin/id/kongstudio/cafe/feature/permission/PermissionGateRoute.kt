package id.kongstudio.cafe.feature.permission

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.permission_action_allow
import id.kongstudio.cafe.resources.permission_bluetooth_description
import id.kongstudio.cafe.resources.permission_bluetooth_title
import id.kongstudio.cafe.resources.permission_camera_description
import id.kongstudio.cafe.resources.permission_camera_title
import id.kongstudio.cafe.resources.permission_location_description
import id.kongstudio.cafe.resources.permission_location_title
import id.kongstudio.cafe.resources.permission_gps_description
import id.kongstudio.cafe.resources.permission_gps_title
import id.kongstudio.cafe.resources.permission_message
import id.kongstudio.cafe.resources.permission_operational_camera_description
import id.kongstudio.cafe.resources.permission_operational_message
import id.kongstudio.cafe.resources.permission_operational_success_message
import id.kongstudio.cafe.resources.permission_status_off
import id.kongstudio.cafe.resources.permission_status_on
import id.kongstudio.cafe.resources.permission_status_denied
import id.kongstudio.cafe.resources.permission_status_granted
import id.kongstudio.cafe.resources.permission_success_message
import id.kongstudio.cafe.resources.permission_success_title
import id.kongstudio.cafe.resources.permission_title
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.permissiongate.PermissionGate
import id.kongstudio.cafe.ui.component.permissiongate.PermissionGateItem
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

private const val SuccessHoldMillis = 1500L

/** Menampilkan [content], dengan panel izin di atasnya selama ada izin [purpose] yang belum diberikan. */
@Composable
internal fun PermissionGateRoute(
    permissions: DevicePermissions,
    purpose: PermissionPurpose,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val status by permissions.status.collectAsState()
    val scope = rememberCoroutineScope()
    val pending = purpose.kinds.filter { status[it] != PermissionStatus.Granted }
    val complete = pending.isEmpty()
    // Panel tetap ada saat tampilan sukses dan animasi keluarnya, tidak hilang seketika.
    var open by remember { mutableStateOf(!complete) }
    var leaving by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { permissions.refresh() }
    LaunchedEffect(complete) {
        if (!complete) {
            open = true
            leaving = false
        } else if (open) {
            delay(SuccessHoldMillis)
            leaving = true
        }
    }

    content()

    if (!open) return

    val granted = stringResource(Res.string.permission_status_granted)
    val denied = stringResource(Res.string.permission_status_denied)
    val gpsOn = stringResource(Res.string.permission_status_on)
    val gpsOff = stringResource(Res.string.permission_status_off)

    // Yang belum siap selalu dimintakan langsung, tanpa dialihkan ke pengaturan.
    fun act(kind: PermissionKind) {
        scope.launch { permissions.request(kind) }
    }

    PermissionGate(
        title = stringResource(Res.string.permission_title),
        message = stringResource(
            when (purpose) {
                PermissionPurpose.Attendance -> Res.string.permission_message
                PermissionPurpose.Operational -> Res.string.permission_operational_message
            },
        ),
        items = purpose.kinds.map { kind ->
            val (title, description) = when (kind) {
                PermissionKind.Location ->
                    stringResource(Res.string.permission_location_title) to
                        stringResource(Res.string.permission_location_description)
                PermissionKind.Camera ->
                    stringResource(Res.string.permission_camera_title) to
                        stringResource(
                            when (purpose) {
                                PermissionPurpose.Attendance -> Res.string.permission_camera_description
                                PermissionPurpose.Operational -> Res.string.permission_operational_camera_description
                            },
                        )
                PermissionKind.Gps ->
                    stringResource(Res.string.permission_gps_title) to
                        stringResource(Res.string.permission_gps_description)
                PermissionKind.Bluetooth ->
                    stringResource(Res.string.permission_bluetooth_title) to
                        stringResource(Res.string.permission_bluetooth_description)
            }
            val isGps = kind == PermissionKind.Gps
            val (statusText, tone) = when (status[kind]) {
                PermissionStatus.Granted -> (if (isGps) gpsOn else granted) to BadgeTone.Positive
                else -> (if (isGps) gpsOff else denied) to BadgeTone.Warning
            }
            val onClick = if (status[kind] == PermissionStatus.Granted) null else ({ act(kind) })
            PermissionGateItem(title, description, statusText, tone, onClick)
        },
        actionLabel = stringResource(Res.string.permission_action_allow),
        onAction = {
            // Satu per satu agar kotak izin sistem tidak saling menimpa.
            scope.launch { pending.forEach { permissions.request(it) } }
        },
        onClosed = {
            open = false
            leaving = false
        },
        visible = !leaving,
        completed = complete,
        completedTitle = stringResource(Res.string.permission_success_title),
        completedMessage = stringResource(
            when (purpose) {
                PermissionPurpose.Attendance -> Res.string.permission_success_message
                PermissionPurpose.Operational -> Res.string.permission_operational_success_message
            },
        ),
        modifier = modifier,
    )
}
