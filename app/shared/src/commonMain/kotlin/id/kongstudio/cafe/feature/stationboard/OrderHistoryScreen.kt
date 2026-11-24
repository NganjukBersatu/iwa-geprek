package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.access.Permission
import id.kongstudio.cafe.feature.access.UserAccess
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.station_kasir_no_session
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Pengajuan batal boleh ditarik pengajunya sendiri, atau oleh yang berhak memutus pengajuan. */
internal fun canWithdrawCancel(access: UserAccess, requestedById: String): Boolean =
    requestedById == access.userId || access.allows(Permission.OrderCancelDecide)

/** Riwayat Pesanan di tablet Mode Kasir: daftar pesanan sesi yang sama dengan tab Kasir di Papan Stasiun, tanpa papan stasiun. */
@Composable
internal fun OrderHistoryScreen(orders: CashierOrdersViewModel?, access: UserAccess, title: String, modifier: Modifier = Modifier) {
    val header: @Composable () -> Unit = {
        Spacer(Modifier.height(AppTheme.spacing.lg))
        PageTitle(title = title)
    }
    if (orders != null) {
        CashierOrdersScreen(
            viewModel = orders,
            canWithdraw = { canWithdrawCancel(access, it.requestedById) },
            listTitle = title,
            header = header,
            modifier = modifier,
        )
        return
    }
    Column(modifier = modifier.fillMaxSize().padding(horizontal = AppTheme.windowSize.pagePadding)) {
        header()
        Spacer(Modifier.height(AppTheme.spacing.md))
        Notice(stringResource(Res.string.station_kasir_no_session))
    }
}
