package id.kongstudio.cafe.feature.sessions

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.feature.ordersync.PendingOrdersGate
import id.kongstudio.cafe.offline.QueueCounts
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.user_sign_out
import id.kongstudio.cafe.resources.user_sign_out_needs_network
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import org.jetbrains.compose.resources.stringResource

/** Lembar keluar tanpa sesi terbuka: hanya tampil selama ada yang menahan, dan karyawan dilepas sendiri begitu antrean bersih. */
@Composable
internal fun SignOutSheet(
    known: Boolean,
    queue: QueueCounts?,
    online: Boolean,
    onReview: () -> Unit,
    onDismiss: () -> Unit,
) {
    AppBottomSheet(title = stringResource(Res.string.user_sign_out), onDismiss = onDismiss) {
        if (!known) InlineMessage(text = stringResource(Res.string.user_sign_out_needs_network))
        PendingOrdersGate(queue = queue, online = online, onReview = onReview)
    }
}
