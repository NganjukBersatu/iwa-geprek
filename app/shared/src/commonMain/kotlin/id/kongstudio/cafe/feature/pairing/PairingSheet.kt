package id.kongstudio.cafe.feature.pairing

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.pairing_sheet_hint
import id.kongstudio.cafe.resources.pairing_sheet_title
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.qrscanner.QrScanner
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Panel pemindai QR; [onScanned] menerima isi QR yang pertama terbaca. */
@Composable
internal fun PairingSheet(
    onScanned: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    AppBottomSheet(
        title = stringResource(Res.string.pairing_sheet_title),
        onDismiss = onDismiss,
    ) {
        QrScanner(onScanned = onScanned)
        Spacer(Modifier.height(AppTheme.spacing.md))
        Notice(stringResource(Res.string.pairing_sheet_hint))
    }
}
