package id.kongstudio.cafe.core.failure

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.failure_login_inactive
import id.kongstudio.cafe.resources.failure_login_invalid
import id.kongstudio.cafe.resources.orders_refresh_failed
import id.kongstudio.cafe.resources.receipt_print_failed
import id.kongstudio.cafe.resources.session_offline
import org.jetbrains.compose.resources.stringResource

/** Teks galat yang bukan hasil panggilan jaringan; layar tetap mengambilnya dari folder ini. */
@Composable
fun staleDataText(): String = stringResource(Res.string.orders_refresh_failed)

@Composable
fun printFailedText(roles: List<String>): String = stringResource(Res.string.receipt_print_failed, roles.joinToString(", "))

@Composable
fun sessionNeedsNetworkText(): String = stringResource(Res.string.session_offline)

/** Teks galat yang dibawa ViewModel sebelum sampai ke layar. */
object FailureTexts {
    val loginInvalid: UiText = UiText.Resource(Res.string.failure_login_invalid)
    val loginInactive: UiText = UiText.Resource(Res.string.failure_login_inactive)
}
