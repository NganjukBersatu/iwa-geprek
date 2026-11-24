package id.kongstudio.cafe.feature.sop

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sop_finish
import id.kongstudio.cafe.resources.sop_next
import id.kongstudio.cafe.resources.sop_previous
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.storyplayer.StoryPage
import id.kongstudio.cafe.ui.component.storyplayer.StoryPlayer
import io.ktor.client.HttpClient
import org.jetbrains.compose.resources.stringResource

@Composable
internal fun SopRoute(
    session: LoginSession,
    client: HttpClient,
    onSessionExpired: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorSopRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "sop-${session.accessToken}") {
        SopViewModel(repository, onSessionExpired)
    }
    val state by viewModel.state.collectAsState()
    val opened = state.opened

    if (opened == null) {
        SopListScreen(
            state = state,
            onOpen = viewModel::open,
            onRetry = viewModel::load,
            onRetryRead = viewModel::retryRead,
            modifier = modifier,
        )
    } else {
        PlatformBackHandler(enabled = true, onBack = viewModel::close)
        StoryPlayer(
            pages = opened.slides.map { StoryPage(title = it.title, body = it.body) },
            title = opened.title,
            previousLabel = stringResource(Res.string.sop_previous),
            nextLabel = stringResource(Res.string.sop_next),
            finishLabel = stringResource(Res.string.sop_finish),
            progressLabel = { current, total -> "$current/$total" },
            onFinish = viewModel::finish,
            modifier = modifier,
        )
    }
}
