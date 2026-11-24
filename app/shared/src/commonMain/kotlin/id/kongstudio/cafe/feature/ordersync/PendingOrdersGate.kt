package id.kongstudio.cafe.feature.ordersync

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.offline.QueueCounts
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.queue_gate_offline
import id.kongstudio.cafe.resources.queue_gate_rejected
import id.kongstudio.cafe.resources.queue_gate_rejected_action
import id.kongstudio.cafe.resources.queue_gate_rejected_title
import id.kongstudio.cafe.resources.queue_gate_sending
import id.kongstudio.cafe.resources.queue_gate_title
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.loadingdots.LoadingDots
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Bagian penahan di lembar tutup sesi dan keluar: tampil selama antrean karyawan belum bersih, kosong bila sudah. */
@Composable
internal fun PendingOrdersGate(
    queue: QueueCounts?,
    online: Boolean,
    onReview: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    if (queue == null || queue.isEmpty) return

    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        if (queue.rejected > 0) {
            AppText(text = stringResource(Res.string.queue_gate_rejected_title), role = TextRole.Section, color = colors.content)
            InlineMessage(text = stringResource(Res.string.queue_gate_rejected, queue.rejected))
            SecondaryButton(text = stringResource(Res.string.queue_gate_rejected_action), onClick = onReview)
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm), verticalAlignment = Alignment.CenterVertically) {
                AppText(text = stringResource(Res.string.queue_gate_title), role = TextRole.Section, color = colors.content)
                LoadingDots(color = colors.primary)
            }
            AppText(
                text = if (online) {
                    stringResource(Res.string.queue_gate_sending, queue.sending)
                } else {
                    stringResource(Res.string.queue_gate_offline)
                },
                role = TextRole.Body,
                color = colors.contentMuted,
            )
        }
    }
}
