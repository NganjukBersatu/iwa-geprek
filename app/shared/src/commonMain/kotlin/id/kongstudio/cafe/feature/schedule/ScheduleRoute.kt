package id.kongstudio.cafe.feature.schedule

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
internal fun ScheduleRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorScheduleRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken), session.user.id)
    }
    val viewModel = viewModel(key = "schedule-${session.accessToken}") {
        ScheduleViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    // Dimuat setiap halaman tampil dan setiap app kembali dari latar belakang, agar data tidak basi.
    LifecycleResumeEffect(viewModel) {
        viewModel.load()
        onPauseOrDispose {}
    }

    ScheduleScreen(
        state = state,
        onSelect = viewModel::select,
        onToggleOnlyMine = viewModel::toggleOnlyMine,
        onPreviousMonth = viewModel::previousMonth,
        onNextMonth = viewModel::nextMonth,
        onRetry = viewModel::load,
        modifier = modifier,
    )
}
