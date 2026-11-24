package id.kongstudio.cafe.feature.leave

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
import io.ktor.client.HttpClient

/** Bagian pengajuan izin karyawan, disisipkan ke halaman yang membutuhkannya. */
@Composable
internal fun LeaveRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorLeaveRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "leave-${session.accessToken}") {
        LeaveViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    // Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
    LifecycleResumeEffect(viewModel) {
        viewModel.load()
        onPauseOrDispose {}
    }

    LeaveSection(
        state = state,
        onRetry = viewModel::load,
        onSubmit = viewModel::submit,
        onCancel = viewModel::cancel,
        onClearError = viewModel::clearError,
        modifier = modifier,
    )
}
