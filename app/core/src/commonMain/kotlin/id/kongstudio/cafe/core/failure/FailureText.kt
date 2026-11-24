package id.kongstudio.cafe.core.failure

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.failure_not_found
import id.kongstudio.cafe.resources.failure_rejected
import id.kongstudio.cafe.resources.failure_secure
import id.kongstudio.cafe.resources.failure_server
import id.kongstudio.cafe.resources.failure_timeout
import id.kongstudio.cafe.resources.failure_unauthorized
import id.kongstudio.cafe.resources.failure_unexpected
import id.kongstudio.cafe.resources.failure_unreachable
import org.jetbrains.compose.resources.stringResource

/** Satu-satunya sumber teks galat untuk pemakai. */
@Composable
fun failureText(failure: AppFailure): String = when (failure) {
    is AppFailure.Unreachable -> stringResource(Res.string.failure_unreachable)
    is AppFailure.Timeout -> stringResource(Res.string.failure_timeout)
    is AppFailure.SecureConnection -> stringResource(Res.string.failure_secure)
    is AppFailure.Unexpected -> stringResource(Res.string.failure_unexpected, failure.kind)
    is AppFailure.Server -> stringResource(Res.string.failure_server, failure.code)
    is AppFailure.NotFound -> stringResource(Res.string.failure_not_found, failure.where, failure.code)
    is AppFailure.Rejected -> failure.message ?: stringResource(Res.string.failure_rejected, failure.code)
    AppFailure.Unauthorized -> stringResource(Res.string.failure_unauthorized)
}
