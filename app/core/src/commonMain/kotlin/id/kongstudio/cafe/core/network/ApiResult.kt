package id.kongstudio.cafe.core.network

import id.kongstudio.cafe.core.failure.AppFailure

sealed interface ApiResult<out T> {
    data class Success<T>(val value: T) : ApiResult<T>

    /** Token ditolak server; sesi harus diakhiri. */
    data object Unauthorized : ApiResult<Nothing>

    data class Failure(val failure: AppFailure) : ApiResult<Nothing>
}
