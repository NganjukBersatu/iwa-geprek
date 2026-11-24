package id.kongstudio.cafe.feature.ordersync

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sync_needs_login
import id.kongstudio.cafe.resources.sync_queued
import id.kongstudio.cafe.resources.sync_rejected
import id.kongstudio.cafe.resources.sync_rejected_action
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Keadaan antrean pesanan di puncak halaman (kosong tidak tampil), dengan yang ditolak diprioritaskan karena butuh keputusan karyawan. */
@Composable
internal fun OrderSyncStatus(viewModel: OrderSyncViewModel, modifier: Modifier = Modifier) {
    val state by viewModel.state.collectAsState()
    val counts = state.counts

    when {
        counts.rejected > 0 -> StatusBanner(
            text = stringResource(Res.string.sync_rejected, counts.rejected),
            tone = BannerTone.Warning,
            actionLabel = stringResource(Res.string.sync_rejected_action),
            onAction = viewModel::openReview,
            modifier = modifier,
        )
        counts.needsLogin > 0 -> StatusBanner(
            text = stringResource(Res.string.sync_needs_login, counts.needsLogin),
            tone = BannerTone.Warning,
            modifier = modifier,
        )
        counts.queued > 0 -> StatusBanner(
            text = stringResource(Res.string.sync_queued, counts.queued),
            icon = AppIcons.WifiOff,
            modifier = modifier,
        )
    }

    if (state.reviewing && state.rejected.isNotEmpty()) {
        RejectedOrdersSheet(
            orders = state.rejected,
            onRetry = viewModel::retry,
            onDiscard = viewModel::discard,
            onDismiss = viewModel::closeReview,
        )
    } else if (state.reviewing) {
        LaunchedEffect(Unit) { viewModel.closeReview() }
    }
}
