package id.kongstudio.cafe.feature.devicesetup

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import id.kongstudio.cafe.feature.permission.DevicePermissions
import id.kongstudio.cafe.feature.permission.PermissionKind
import id.kongstudio.cafe.feature.permission.PermissionStatus
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.device_setup_code_label
import id.kongstudio.cafe.resources.device_setup_code_placeholder
import id.kongstudio.cafe.resources.device_setup_or_type
import id.kongstudio.cafe.resources.device_setup_scan
import id.kongstudio.cafe.resources.device_setup_scan_hint
import id.kongstudio.cafe.resources.device_setup_scan_invalid
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.qrscanner.QrScanner
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

// Isi QR perangkat yang dibuat web admin; kode setelah awalan sama dengan kode yang bisa diketik.
private const val PairQrPrefix = "camera-pair:"

/** Kode perangkat dari isi QR; null bila QR itu bukan QR pemasangan perangkat. */
internal fun deviceCodeOf(scanned: String): String? =
    scanned.trim().takeIf { it.startsWith(PairQrPrefix) }?.removePrefix(PairQrPrefix)?.trim()?.takeIf { it.isNotEmpty() }

/**
 * Panel kode perangkat dengan satu tombol; dipakai untuk mendaftarkan dan melepas. Bila [permissions] diberikan, panel juga
 * bisa memindai QR dari web admin, dengan izin kamera diminta saat tombol pindai ditekan dan kode ketik tetap sebagai cadangan.
 */
@Composable
internal fun DeviceCodeSheet(
    title: String,
    description: String,
    actionLabel: String,
    onSubmit: (String) -> Unit,
    onDismiss: () -> Unit,
    errorText: String? = null,
    enabled: Boolean = true,
    permissions: DevicePermissions? = null,
) {
    var code by remember { mutableStateOf("") }
    var scanning by remember { mutableStateOf(false) }
    var invalidScan by remember { mutableStateOf(false) }
    // QR yang sama terbaca berkali-kali per detik; hanya kode baru yang dikirim.
    var lastScanned by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val spacing = AppTheme.spacing
    val cameraStatus = permissions?.status?.collectAsState()?.value?.get(PermissionKind.Camera)

    AppBottomSheet(title = title, onDismiss = onDismiss) {
        AppText(text = description, role = TextRole.Body, color = AppTheme.colors.contentMuted)

        if (permissions != null) {
            Spacer(Modifier.height(spacing.lg))
            if (scanning && cameraStatus == PermissionStatus.Granted) {
                QrScanner(onScanned = { scanned ->
                    if (!enabled || scanned == lastScanned) return@QrScanner
                    lastScanned = scanned
                    val scannedCode = deviceCodeOf(scanned)
                    invalidScan = scannedCode == null
                    scannedCode?.let(onSubmit)
                })
                Spacer(Modifier.height(spacing.md))
                Notice(stringResource(Res.string.device_setup_scan_hint))
            } else {
                PrimaryButton(
                    text = stringResource(Res.string.device_setup_scan),
                    icon = AppIcons.Camera,
                    onClick = {
                        scope.launch {
                            if (permissions.status.value[PermissionKind.Camera] != PermissionStatus.Granted) permissions.request(PermissionKind.Camera)
                            scanning = true
                        }
                    },
                    enabled = enabled,
                )
            }
            if (invalidScan) {
                Spacer(Modifier.height(spacing.md))
                InlineMessage(text = stringResource(Res.string.device_setup_scan_invalid))
            }
            Spacer(Modifier.height(spacing.lg))
            AppText(text = stringResource(Res.string.device_setup_or_type), role = TextRole.Label, color = AppTheme.colors.contentMuted)
            Spacer(Modifier.height(spacing.sm))
        } else {
            Spacer(Modifier.height(spacing.lg))
        }

        val submit: () -> Unit = { onSubmit(code.trim()) }
        AppTextField(
            value = code,
            onValueChange = { code = it },
            label = stringResource(Res.string.device_setup_code_label),
            placeholder = stringResource(Res.string.device_setup_code_placeholder),
            isError = errorText != null,
            // Kode diketik huruf besar dan tombol Selesai di papan ketik langsung mengirimnya, sama seperti tombol di bawah.
            keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Characters, autoCorrectEnabled = false, imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = { if (enabled && code.isNotBlank()) submit() }),
        )

        if (errorText != null) {
            Spacer(Modifier.height(spacing.md))
            InlineMessage(text = errorText)
        }

        Spacer(Modifier.height(spacing.lg))
        if (permissions != null) {
            SecondaryButton(text = actionLabel, onClick = submit, enabled = enabled && code.isNotBlank())
        } else {
            PrimaryButton(text = actionLabel, onClick = submit, enabled = enabled && code.isNotBlank())
        }
    }
}
