package id.kongstudio.cafe.feature.auth.login

import id.kongstudio.cafe.core.text.UiText

data class LoginUiState(
    val username: String = "",
    val password: String = "",
    val submitting: Boolean = false,
    val error: UiText? = null,
) {
    val canSubmit: Boolean
        get() = !submitting && username.isNotBlank() && password.isNotBlank()
}
