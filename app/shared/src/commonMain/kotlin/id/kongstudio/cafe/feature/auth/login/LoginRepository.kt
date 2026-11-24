package id.kongstudio.cafe.feature.auth.login

import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.auth.session.LoginSession

sealed interface LoginResult {
    data class Success(val session: LoginSession) : LoginResult

    /** 401: username atau password salah. */
    data object InvalidCredentials : LoginResult

    /** 403: akun dinonaktifkan. */
    data object AccountInactive : LoginResult

    /** Tidak sampai ke server atau server menjawab di luar 200, 401, dan 403. */
    data class Failed(val failure: AppFailure) : LoginResult
}

interface LoginRepository {
    suspend fun login(username: String, password: String): LoginResult
}
