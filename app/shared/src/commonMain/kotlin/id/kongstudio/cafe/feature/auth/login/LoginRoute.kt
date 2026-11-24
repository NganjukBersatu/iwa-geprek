package id.kongstudio.cafe.feature.auth.login

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.devicesetup.DeviceCodeSheet
import id.kongstudio.cafe.feature.permission.DevicePermissions
import id.kongstudio.cafe.feature.devicesetup.DevicePairingResult
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.device_setup_action
import id.kongstudio.cafe.resources.device_setup_description
import id.kongstudio.cafe.resources.device_setup_menu
import id.kongstudio.cafe.resources.device_setup_title
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

@Composable
fun LoginRoute(
    repository: LoginRepository,
    onLoggedIn: (LoginSession) -> Unit,
    onRegisterDevice: suspend (String) -> DevicePairingResult,
    permissions: DevicePermissions,
    modifier: Modifier = Modifier,
) {
    val viewModel = viewModel { LoginViewModel(repository) }
    val state by viewModel.state.collectAsState()
    val session by viewModel.session.collectAsState()
    var deviceSetupOpen by rememberSaveable { mutableStateOf(false) }
    var deviceSetupBusy by remember { mutableStateOf(false) }
    var deviceSetupResult by remember { mutableStateOf<DevicePairingResult?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(session) {
        session?.let {
            viewModel.consumeSession()
            onLoggedIn(it)
        }
    }

    LoginScreen(
        state = state,
        onUsernameChange = viewModel::onUsernameChange,
        onPasswordChange = viewModel::onPasswordChange,
        onSubmit = viewModel::submit,
        modifier = modifier,
        topAction = {
            AppIconButton(
                icon = AppIcons.Dots,
                contentDescription = stringResource(Res.string.device_setup_menu),
                onClick = {
                    deviceSetupResult = null
                    deviceSetupOpen = true
                },
                tint = AppTheme.colors.primary,
            )
        },
    )

    if (deviceSetupOpen) {
        val errorText = (deviceSetupResult as? DevicePairingResult.Failed)?.let { failureText(it.failure) }
        DeviceCodeSheet(
            title = stringResource(Res.string.device_setup_title),
            description = stringResource(Res.string.device_setup_description),
            actionLabel = stringResource(Res.string.device_setup_action),
            errorText = errorText,
            enabled = !deviceSetupBusy,
            onSubmit = { code ->
                scope.launch {
                    deviceSetupBusy = true
                    val result = onRegisterDevice(code)
                    deviceSetupBusy = false
                    deviceSetupResult = result
                    // Bila berhasil, App berpindah ke halaman operasional dan login ini hilang.
                    if (result is DevicePairingResult.Paired) deviceSetupOpen = false
                }
            },
            onDismiss = { deviceSetupOpen = false },
            permissions = permissions,
        )
    }
}
