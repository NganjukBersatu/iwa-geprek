package id.kongstudio.cafe.feature.profile

import androidx.compose.runtime.getValue
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiConfig
import id.kongstudio.cafe.feature.auth.session.LoginSession
import io.ktor.client.HttpClient

@Composable
internal fun ProfileRoute(
    session: LoginSession,
    client: HttpClient,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val repository = remember(session.accessToken) {
        KtorProfileRepository(ApiCaller(client, ApiConfig.V2_BASE_URL, session.accessToken))
    }
    val viewModel = viewModel(key = "profile-${session.accessToken}") {
        ProfileViewModel(repository, onSessionExpired = onLogout)
    }
    val state by viewModel.state.collectAsState()

    ProfileScreen(
        state = state,
        fallbackName = session.user.name ?: session.user.username,
        fallbackRole = session.user.roleName,
        onFormChange = viewModel::onFormChange,
        onSave = viewModel::save,
        onOldPasswordChange = viewModel::onOldPasswordChange,
        onNewPasswordChange = viewModel::onNewPasswordChange,
        onConfirmPasswordChange = viewModel::onConfirmPasswordChange,
        onChangePassword = viewModel::changePassword,
        onUploadPhoto = viewModel::uploadPhoto,
        onDeletePhoto = viewModel::deletePhoto,
        onClearPhotoError = viewModel::clearPhotoError,
        onRetry = viewModel::load,
        onLogout = onLogout,
        modifier = modifier,
    )
}
