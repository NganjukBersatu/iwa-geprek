package id.kongstudio.cafe.ui.component.failurestate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_retry
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Keadaan gagal memuat: teks dari sebab sebenarnya ([failureText]) dan tombol coba lagi bila [onRetry] diberi, kecuali sesi berakhir. */
@Composable
fun FailureState(
    failure: AppFailure,
    modifier: Modifier = Modifier,
    onRetry: (() -> Unit)? = null,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
    ) {
        Notice(failureText(failure))
        if (onRetry != null && failure != AppFailure.Unauthorized) {
            PrimaryButton(text = stringResource(Res.string.common_retry), onClick = onRetry)
        }
    }
}
