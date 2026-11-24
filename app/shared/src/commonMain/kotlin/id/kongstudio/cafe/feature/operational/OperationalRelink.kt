package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.ui.component.screenbackdrop.ScreenBackdrop
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.operational_relink_action
import id.kongstudio.cafe.resources.operational_relink_message
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Identitas karyawan tidak tersedia; satu-satunya jalan adalah memindai ulang QR. */
@Composable
internal fun OperationalRelink(onRelink: () -> Unit, modifier: Modifier = Modifier) {
    ScreenBackdrop(modifier = modifier) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(AppTheme.windowSize.pagePadding),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.lg, Alignment.CenterVertically),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Notice(stringResource(Res.string.operational_relink_message))
            PrimaryButton(
                text = stringResource(Res.string.operational_relink_action),
                onClick = onRelink,
                modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth),
            )
        }
    }
}
