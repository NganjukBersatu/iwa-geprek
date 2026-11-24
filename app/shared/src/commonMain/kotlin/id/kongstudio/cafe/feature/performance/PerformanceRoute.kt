package id.kongstudio.cafe.feature.performance

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

@Composable
internal fun PerformanceRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorPerformanceRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "performance-${session.accessToken}") {
        PerformanceViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    // Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
    LifecycleResumeEffect(viewModel) {
        viewModel.retry()
        onPauseOrDispose {}
    }

    PerformanceScreen(
        state = state,
        onSelectRange = viewModel::select,
        onRetry = viewModel::retry,
        modifier = modifier,
    )
}
