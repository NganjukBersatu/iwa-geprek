package id.kongstudio.cafe.feature.auth.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.FailureTexts
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.feature.auth.session.LoginSession
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class LoginViewModel(private val repository: LoginRepository) : ViewModel() {
    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    private val _session = MutableStateFlow<LoginSession?>(null)
    val session: StateFlow<LoginSession?> = _session.asStateFlow()

    fun onUsernameChange(value: String) {
        _state.update { it.copy(username = value, error = null) }
    }

    fun onPasswordChange(value: String) {
        _state.update { it.copy(password = value, error = null) }
    }

    fun submit() {
        val current = _state.value
        if (!current.canSubmit) return
        _state.update { it.copy(submitting = true, error = null) }
        viewModelScope.launch {
            try {
                when (val result = repository.login(current.username, current.password)) {
                    is LoginResult.Success -> _session.value = result.session
                    LoginResult.InvalidCredentials -> showError(FailureTexts.loginInvalid)
                    LoginResult.AccountInactive -> showError(FailureTexts.loginInactive)
                    is LoginResult.Failed -> showError(UiText.Failed(result.failure))
                }
            } finally {
                _state.update { it.copy(submitting = false) }
            }
        }
    }

    /** Dipanggil setelah sesi diserahkan, agar ViewModel yang hidup sepanjang Activity tidak memasangnya lagi saat logout. */
    fun consumeSession() {
        _session.value = null
        _state.update { it.copy(password = "") }
    }

    private fun showError(message: UiText) {
        _state.update { it.copy(error = message) }
    }
}
