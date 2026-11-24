package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_cancel
import id.kongstudio.cafe.resources.station_cancel_hint
import id.kongstudio.cafe.resources.station_cancel_reason
import id.kongstudio.cafe.resources.station_cancel_request
import id.kongstudio.cafe.resources.station_cancel_send
import id.kongstudio.cafe.resources.station_cancel_summary
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

// Formulir pengajuan pembatalan; alasan boleh kosong, pembatalan baru berlaku setelah disetujui di web.
@Composable
internal fun CancelRequestSheet(
    receipt: String,
    total: Long,
    sending: Boolean,
    failure: AppFailure?,
    onSend: (reason: String) -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = AppTheme.colors
    var reason by rememberSaveable { mutableStateOf("") }

    AppBottomSheet(
        title = stringResource(Res.string.station_cancel_request),
        onDismiss = onDismiss,
        dismissible = !sending,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppText(
                text = stringResource(Res.string.station_cancel_summary, "#$receipt", formatRupiah(total)),
                role = TextRole.Body,
                color = colors.content,
            )
            AppTextField(
                value = reason,
                onValueChange = { reason = it },
                label = stringResource(Res.string.station_cancel_reason),
                enabled = !sending,
            )
            AppText(
                text = stringResource(Res.string.station_cancel_hint),
                role = TextRole.Caption,
                color = colors.contentMuted,
            )
            failure?.let { InlineMessage(text = failureText(it)) }
            PrimaryButton(
                text = stringResource(Res.string.station_cancel_send),
                onClick = { onSend(reason) },
                enabled = !sending,
                loading = sending,
                containerColor = colors.danger,
            )
            SecondaryButton(
                text = stringResource(Res.string.common_cancel),
                onClick = onDismiss,
                tone = ButtonTone.Cancel,
                enabled = !sending,
            )
        }
    }
}
