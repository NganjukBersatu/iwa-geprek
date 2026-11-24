package id.kongstudio.cafe.feature.mysession

import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.core.format.DateTimeFormat
import androidx.compose.runtime.getValue
import id.kongstudio.cafe.ui.component.pagetitle.PageTitle
import id.kongstudio.cafe.ui.component.pageframe.PageFrame
import id.kongstudio.cafe.core.format.formatRupiah
import id.kongstudio.cafe.core.format.formatRupiahCompact
import id.kongstudio.cafe.feature.sessions.SessionItem
import id.kongstudio.cafe.feature.sessions.sessionDetailRows
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.feature.admin.PagedListViewModel
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_no_shift
import id.kongstudio.cafe.resources.nav_my_session
import id.kongstudio.cafe.resources.orders_refresh
import id.kongstudio.cafe.resources.session_cash_revenue
import id.kongstudio.cafe.resources.session_chart_composition
import id.kongstudio.cafe.resources.session_chart_trend
import id.kongstudio.cafe.resources.session_close
import id.kongstudio.cafe.resources.session_noncash_revenue
import id.kongstudio.cafe.resources.session_last
import id.kongstudio.cafe.resources.session_open
import id.kongstudio.cafe.resources.session_running
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.columnchart.ColumnChart
import id.kongstudio.cafe.ui.component.detailcard.DetailCard
import id.kongstudio.cafe.ui.component.donutchart.DonutChart
import id.kongstudio.cafe.ui.component.donutchart.DonutSlice
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.loadable.Loadable
import id.kongstudio.cafe.ui.component.loadable.LoadingVariant
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource


/** Sesi kas karyawan pemegang tablet: sesi berjalan, tombol buka atau tutup, sesi terakhir, dan riwayatnya, dengan [activeId] yang berubah memuat ulang angkanya. */
@Composable
internal fun MySessionScreen(
    viewModel: MySessionViewModel,
    history: PagedListViewModel<SessionItem>,
    activeId: String?,
    canControl: Boolean,
    onOpen: () -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val state by viewModel.state.collectAsState()
    val detail by viewModel.detail.collectAsState()
    val spacing = AppTheme.spacing
    var loadedFor by remember { mutableStateOf(activeId) }

    LaunchedEffect(activeId) {
        viewModel.refresh()
        // Daftar riwayat sudah memuat sendiri saat dibuat; dimuat ulang hanya saat sesi dibuka atau ditutup.
        if (activeId != loadedFor) {
            loadedFor = activeId
            history.reload()
        }
    }

    PageFrame(modifier = modifier) {
            item {
                PageTitle(title = stringResource(Res.string.nav_my_session)) {
                    if (state.running != null) {
                        StatusBadge(text = stringResource(Res.string.session_running), tone = BadgeTone.Positive)
                    }
                    AppIconButton(
                        icon = AppIcons.Refresh,
                        contentDescription = stringResource(Res.string.orders_refresh),
                        onClick = viewModel::refresh,
                    )
                }
            }
            item {
                Loadable(loading = state.loading, variant = LoadingVariant.Detail) {
                    val failure = state.failure
                    if (failure != null) {
                        FailureState(failure = failure, onRetry = viewModel::refresh)
                    } else {
                        Column(verticalArrangement = Arrangement.spacedBy(spacing.md)) {
                            val running = state.running
                            if (running != null) {
                                DetailCard(rows = sessionDetailRows(running))
                                if (canControl) SecondaryButton(text = stringResource(Res.string.session_close), onClick = onClose, tone = ButtonTone.Danger)
                                SessionMoneyCharts(session = running, methods = state.methods[running.id] ?: MethodsState.Loading)
                            } else {
                                Notice(stringResource(Res.string.cashier_no_shift))
                                if (canControl) PrimaryButton(text = stringResource(Res.string.session_open), onClick = onOpen)
                            }
                            // Tanpa pendapatan sama sekali, grafik tren hanya berisi sumbu kosong, jadi tidak ditampilkan.
                            if (state.recent.any { it.revenue > 0 }) {
                                SectionTitle(text = stringResource(Res.string.session_chart_trend))
                                ColumnChart(
                                    values = state.recent.map { it.revenue },
                                    labels = state.recent.map { sessionDayLabel(it) },
                                    axisText = ::formatRupiahCompact,
                                )
                            }
                            state.last?.let { last ->
                                SectionTitle(text = stringResource(Res.string.session_last))
                                DetailCard(rows = sessionDetailRows(last))
                                SessionMoneyCharts(session = last, methods = state.methods[last.id] ?: MethodsState.Loading)
                            }
                        }
                    }
                }
            }
            item { SessionHistorySection(history = history, onOpen = viewModel::openDetail) }
    }

    detail?.let { SessionDetailSheet(detail = it, onRetry = viewModel::retryOrders, onDismiss = viewModel::closeDetail) }
}

/** Tanggal pendek sesi, misalnya 16/10, untuk sumbu grafik. */
private fun sessionDayLabel(session: SessionItem): String {
    val date = DateTimeFormat.stamp(session.startedAt)?.date ?: return ""
    return "${DateTimeFormat.dayOfMonth(date)}/${DateTimeFormat.monthIndex(date) + 1}"
}
