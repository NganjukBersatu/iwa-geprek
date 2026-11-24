package id.kongstudio.cafe.feature.sessions

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.core.failure.sessionNeedsNetworkText
import id.kongstudio.cafe.resources.session_open
import id.kongstudio.cafe.resources.session_form_opening_cash
import id.kongstudio.cafe.ui.component.formsheet.FormSheet
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.moneyfield.MoneyField
import id.kongstudio.cafe.resources.session_opening_required
import id.kongstudio.cafe.resources.form_invalid_check_above
import org.jetbrains.compose.resources.stringResource

/** Lembar buka sesi: modal awal laci, ditahan selama status sesi belum terbaca dari server. */
@Composable
internal fun OpenSessionSheet(
    known: Boolean,
    submitting: Boolean,
    failure: AppFailure?,
    onSubmit: (Long) -> Unit,
    onDismiss: () -> Unit,
) {
    var amount by remember { mutableStateOf<Long?>(null) }

    FormSheet(
        title = stringResource(Res.string.session_open),
        submitLabel = stringResource(Res.string.session_open),
        onSubmit = { onSubmit(amount ?: 0L) },
        onDismiss = onDismiss,
        submitting = submitting,
        canSubmit = known && amount != null,
        invalidMessage = stringResource(if (known) Res.string.session_opening_required else Res.string.form_invalid_check_above),
        error = failure?.let { failureText(it) },
    ) {
        if (!known) Notice(sessionNeedsNetworkText())
        MoneyField(
            amount = amount,
            onAmountChange = { amount = it },
            label = stringResource(Res.string.session_form_opening_cash),
        )
    }
}
