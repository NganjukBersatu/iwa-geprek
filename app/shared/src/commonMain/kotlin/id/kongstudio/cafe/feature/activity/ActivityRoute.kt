package id.kongstudio.cafe.feature.activity

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import io.ktor.client.HttpClient

@Composable
internal fun ActivityRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorActivityRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "activity-${session.accessToken}") {
        ActivityViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()

    ActivityScreen(
        state = state,
        onSelectGroup = viewModel::select,
        onPageChange = viewModel::setPage,
        onRetry = viewModel::retry,
        modifier = modifier,
    )
}
