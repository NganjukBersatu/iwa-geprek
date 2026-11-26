package id.kongstudio.cafe.feature.devicesetup

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.feature.permission.DevicePermissions
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_retry
import id.kongstudio.cafe.resources.device_repair_action
import id.kongstudio.cafe.resources.device_repair_description
import id.kongstudio.cafe.resources.device_repair_title
import id.kongstudio.cafe.resources.device_unpaired_enter
import id.kongstudio.cafe.resources.device_unpaired_message
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.screenbackdrop.ScreenBackdrop
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

/**
 * Layar penuh saat server menjawab bahwa token tablet ini sudah tidak berlaku, misalnya karena kodenya dipakai perangkat lain.
 * Kode pasang dari web admin memasangkan perangkat ini lagi tanpa keluar akun; [onRetry] menutup layar dan membiarkan permintaan berikutnya memeriksa ulang.
 */
@Composable
internal fun DeviceUnpairedGate(
    onRepair: suspend (String) -> DevicePairingResult,
    onRetry: () -> Unit,
    permissions: DevicePermissions,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val scope = rememberCoroutineScope()
    var sheetOpen by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf<DevicePairingResult.Failed?>(null) }

    ScreenBackdrop(modifier = modifier) {
        Column(
            modifier = Modifier
                .align(Alignment.Center)
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.xxxl),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(spacing.lg),
        ) {
            AppText(
                text = stringResource(Res.string.device_unpaired_message),
                role = TextRole.Body,
                color = AppTheme.colors.content,
                textAlign = TextAlign.Center,
            )
            PrimaryButton(
                text = stringResource(Res.string.device_unpaired_enter),
                onClick = {
                    failed = null
                    sheetOpen = true
                },
            )
            SecondaryButton(text = stringResource(Res.string.common_retry), onClick = onRetry)
        }
    }

    if (sheetOpen) {
        DeviceCodeSheet(
            title = stringResource(Res.string.device_repair_title),
            description = stringResource(Res.string.device_repair_description),
            actionLabel = stringResource(Res.string.device_repair_action),
            errorText = failed?.let { failureText(it.failure) },
            enabled = !busy,
            onSubmit = { code ->
                scope.launch {
                    busy = true
                    val result = onRepair(code)
                    busy = false
                    // Bila berhasil, App membangun ulang halaman operasional dan layar ini hilang.
                    failed = result as? DevicePairingResult.Failed
                    if (result is DevicePairingResult.Paired) sheetOpen = false
                }
            },
            onDismiss = { sheetOpen = false },
            permissions = permissions,
        )
    }
}
