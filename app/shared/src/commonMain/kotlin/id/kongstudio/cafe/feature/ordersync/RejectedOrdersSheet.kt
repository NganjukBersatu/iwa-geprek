package id.kongstudio.cafe.feature.ordersync

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.offline.QueuedOrder
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sync_discard
import id.kongstudio.cafe.resources.sync_item_count
import id.kongstudio.cafe.resources.sync_reason_unknown
import id.kongstudio.cafe.resources.sync_rejected_title
import id.kongstudio.cafe.resources.sync_retry
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.theme.AppTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.resources.offline_discard_confirm
import id.kongstudio.cafe.resources.offline_discard_message
import id.kongstudio.cafe.resources.offline_discard_title
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import org.jetbrains.compose.resources.stringResource

/** Pesanan yang ditolak server: karyawan memutuskan kirim ulang atau hapus, tidak ada yang berjalan sendiri. */
@Composable
internal fun RejectedOrdersSheet(
    orders: List<QueuedOrder>,
    onRetry: (clientId: String) -> Unit,
    onDiscard: (clientId: String) -> Unit,
    onDismiss: () -> Unit,
) {
    val spacing = AppTheme.spacing
    var discarding by remember { mutableStateOf<QueuedOrder?>(null) }

    AppBottomSheet(title = stringResource(Res.string.sync_rejected_title), onDismiss = onDismiss) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(spacing.md)) {
            orders.forEach { order ->
                ListCard {
                    ListRow(
                        title = formatRupiah(order.total),
                        detail = stringResource(Res.string.sync_item_count, order.itemCount),
                        caption = order.message ?: stringResource(Res.string.sync_reason_unknown),
                        footnote = DateTimeFormat.stampAt(order.createdEpoch).time,
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(spacing.md),
                        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                    ) {
                        SecondaryButton(
                            text = stringResource(Res.string.sync_discard),
                            onClick = { discarding = order },
                            tone = ButtonTone.Danger,
                            modifier = Modifier.weight(1f),
                        )
                        PrimaryButton(
                            text = stringResource(Res.string.sync_retry),
                            onClick = { onRetry(order.clientId) },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }
    }

    // Membuang pesanan tidak bisa dibatalkan, jadi selalu dikonfirmasi seperti di rincian Mode Offline.
    discarding?.let { order ->
        ConfirmSheet(
            title = stringResource(Res.string.offline_discard_title),
            message = stringResource(Res.string.offline_discard_message, formatRupiah(order.total)),
            confirmLabel = stringResource(Res.string.offline_discard_confirm),
            onConfirm = {
                discarding = null
                onDiscard(order.clientId)
            },
            onDismiss = { discarding = null },
            destructive = true,
        )
    }
}
