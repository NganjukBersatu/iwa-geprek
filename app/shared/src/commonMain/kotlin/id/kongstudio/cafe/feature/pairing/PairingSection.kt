package id.kongstudio.cafe.feature.pairing

import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.pairing_action
import id.kongstudio.cafe.resources.pairing_description
import id.kongstudio.cafe.resources.pairing_success_message
import id.kongstudio.cafe.resources.pairing_success_title
import id.kongstudio.cafe.resources.pairing_title
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.successstate.SuccessState
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import io.ktor.client.HttpClient
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

/** Bagian halaman Absen untuk menautkan karyawan ke perangkat operasional lewat pindai QR. */
@Composable
internal fun ColumnScope.PairingSection(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
) {
    val repository = remember(session.accessToken) {
        KtorPairingRepository(client, ApiConfig.V2_BASE_URL, session.accessToken)
    }
    val scope = rememberCoroutineScope()
    var scanning by rememberSaveable { mutableStateOf(false) }
    var sending by remember { mutableStateOf(false) }
    var linked by remember { mutableStateOf<LinkedDevice?>(null) }
    var failure by remember { mutableStateOf<AppFailure?>(null) }
    val spacing = AppTheme.spacing

    val connected = linked
    when {
        sending -> LoadingState(modifier = Modifier.padding(top = spacing.xl), rows = 2)
        connected != null -> SuccessState(
            title = stringResource(Res.string.pairing_success_title),
            message = stringResource(Res.string.pairing_success_message, connected.name),
            icon = AppIcons.Checklist,
            modifier = Modifier.padding(top = spacing.xl),
        )
        else -> ListCard(modifier = Modifier.padding(top = spacing.xl)) {
            ListRow(
                title = stringResource(Res.string.pairing_title),
                caption = stringResource(Res.string.pairing_description),
            )
        }
    }

    failure?.let {
        Spacer(Modifier.height(spacing.md))
        InlineMessage(text = failureText(it))
    }

    if (connected == null) {
        Spacer(Modifier.height(spacing.md))
        SecondaryButton(
            text = stringResource(Res.string.pairing_action),
            onClick = {
                failure = null
                scanning = true
            },
            enabled = !sending,
        )
    }

    if (scanning) {
        PairingSheet(
            onScanned = { qrToken ->
                // Pemindai memanggil berulang untuk QR yang sama; hanya yang pertama diproses.
                if (!scanning || sending) return@PairingSheet
                scanning = false
                sending = true
                scope.launch {
                    when (val result = repository.link(qrToken)) {
                        is DeviceResult.Ok -> linked = result.value
                        is DeviceResult.Failed ->
                            if (result.failure == AppFailure.Unauthorized) {
                                onSessionExpired()
                            } else {
                                failure = result.failure
                            }
                    }
                    sending = false
                }
            },
            onDismiss = { scanning = false },
        )
    }
}
