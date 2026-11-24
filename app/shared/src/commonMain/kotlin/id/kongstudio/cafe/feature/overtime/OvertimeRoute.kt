package id.kongstudio.cafe.feature.overtime

import id.kongstudio.cafe.feature.access.Permission
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.dayplan.DayPlanLink
import io.ktor.client.HttpClient

/** Bagian lembur karyawan, disisipkan ke halaman yang membutuhkannya. */
@Composable
internal fun OvertimeRoute(
    session: LoginSession,
    client: HttpClient,
    plan: DayPlanLink,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorOvertimeRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "overtime-${session.accessToken}") {
        OvertimeViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    // Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
    LifecycleResumeEffect(viewModel) {
        viewModel.load()
        onPauseOrDispose {}
    }

    OvertimeSection(
        state = state,
        canRecord = session.user.can(Permission.OvertimeSelf),
        scheduledOvertime = plan.scheduledOvertime,
        onRetry = viewModel::load,
        onRecord = { request, onSuccess ->
            viewModel.record(request) {
                onSuccess()
                plan.reload()
            }
        },
        onPageChange = viewModel::setPage,
        onClearError = viewModel::clearError,
        modifier = modifier,
    )
}
