package id.kongstudio.cafe.feature.update

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.update_continue_session
import id.kongstudio.cafe.resources.update_installed
import id.kongstudio.cafe.resources.update_message
import id.kongstudio.cafe.resources.update_message_session
import id.kongstudio.cafe.resources.update_minimum
import id.kongstudio.cafe.resources.update_no_link
import id.kongstudio.cafe.resources.update_open_download
import id.kongstudio.cafe.resources.update_session_note
import id.kongstudio.cafe.resources.update_title
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.statusbanner.BannerTone
import id.kongstudio.cafe.ui.component.statusbanner.StatusBanner
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Modal pembaruan wajib yang tidak bisa ditutup; kasir dengan sesi berjalan boleh melanjutkan sampai sesinya ditutup. */
@Composable
internal fun UpdateGate(update: AppUpdate) {
    val state by update.state.collectAsState()
    if (!state.locked) return
    val spacing = AppTheme.spacing
    val uriHandler = LocalUriHandler.current
    val url = state.downloadUrl

    AppDialog(title = stringResource(Res.string.update_title), onDismiss = {}, dismissible = false) {
        Column(
            modifier = Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(spacing.lg),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            AppText(text = stringResource(if (state.sessionOpen) Res.string.update_message_session else Res.string.update_message))
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                VersionBox(label = stringResource(Res.string.update_installed), value = update.installed, valueColor = AppTheme.colors.danger, modifier = Modifier.weight(1f))
                state.minimum?.let { VersionBox(label = stringResource(Res.string.update_minimum), value = it, valueColor = AppTheme.colors.content, modifier = Modifier.weight(1f)) }
            }
            if (state.sessionOpen) StatusBanner(text = stringResource(Res.string.update_session_note), tone = BannerTone.Warning)
            if (url != null) {
                PrimaryButton(text = stringResource(Res.string.update_open_download), onClick = { uriHandler.openUri(url) })
            } else {
                AppText(text = stringResource(Res.string.update_no_link), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            }
            if (state.sessionOpen) SecondaryButton(text = stringResource(Res.string.update_continue_session), onClick = update::defer)
        }
    }
}

@Composable
private fun VersionBox(label: String, value: String, valueColor: Color, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.clip(AppTheme.shapes.field).background(AppTheme.colors.surface).padding(AppTheme.spacing.md),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        AppText(text = label, role = TextRole.Caption, color = AppTheme.colors.contentMuted, maxLines = 1)
        AppText(text = value, role = TextRole.Title, color = valueColor)
    }
}
