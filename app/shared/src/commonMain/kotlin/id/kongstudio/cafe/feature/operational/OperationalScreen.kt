package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.ui.component.screenbackdrop.ScreenBackdrop
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.apptext.AppText
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.core.failure.failureText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.device_setup_menu
import id.kongstudio.cafe.resources.operational_qr_closed
import id.kongstudio.cafe.resources.operational_qr_show
import id.kongstudio.cafe.resources.operational_refresh
import id.kongstudio.cafe.resources.operational_step_aim
import id.kongstudio.cafe.resources.operational_step_open
import id.kongstudio.cafe.resources.operational_step_scan
import id.kongstudio.cafe.resources.operational_title
import id.kongstudio.cafe.resources.shell_rail_subtitle
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.divideditems.DividedItems
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.notice.Notice
import id.kongstudio.cafe.ui.component.qrcode.QrCode
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource


/** Layar penuh tablet operasional: QR pairing, hitung mundur, dan langkah singkat; setelah lama tanpa pemindaian QR ditutup dan tampil lagi lewat tombol. */
@Composable
internal fun OperationalScreen(
    state: OperationalUiState,
    onMenu: () -> Unit,
    onShowQr: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val steps = listOf(
        stringResource(Res.string.operational_step_open),
        stringResource(Res.string.operational_step_scan),
        stringResource(Res.string.operational_step_aim),
    )

    ScreenBackdrop(modifier = modifier) {
        Column(
            modifier = Modifier
                .align(Alignment.Center)
                .widthIn(max = AppTheme.sizes.contentMaxWidth)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.xxxl),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(spacing.lg),
        ) {
            AppText(
                text = stringResource(Res.string.operational_title),
                role = TextRole.Headline,
                color = colors.content,
                textAlign = TextAlign.Center,
            )
            AppText(
                text = stringResource(Res.string.shell_rail_subtitle),
                role = TextRole.Body,
                color = colors.contentMuted,
                textAlign = TextAlign.Center,
            )

            val token = state.token
            when {
                state.closed -> {
                    Notice(stringResource(Res.string.operational_qr_closed))
                    PrimaryButton(text = stringResource(Res.string.operational_qr_show), onClick = onShowQr)
                }
                token != null -> {
                    QrCode(
                        content = token,
                        modifier = Modifier
                            .widthIn(max = AppTheme.sizes.qrMaxWidth)
                            .fillMaxWidth()
                            .clip(AppTheme.shapes.card),
                    )
                    AppText(
                        text = stringResource(Res.string.operational_refresh, countdown(state.secondsLeft)),
                        role = TextRole.Label,
                        color = colors.contentMuted,
                        textAlign = TextAlign.Center,
                    )
                }
                state.failure != null -> Notice(failureText(state.failure))
                else -> LoadingState()
            }

            ListCard {
                DividedItems(steps) { step -> ListRow(title = step) }
            }
        }

        AppIconButton(
            icon = AppIcons.Dots,
            contentDescription = stringResource(Res.string.device_setup_menu),
            onClick = onMenu,
            tint = colors.primary,
            modifier = Modifier.align(Alignment.TopEnd).padding(spacing.sm),
        )
    }
}

private fun countdown(seconds: Int): String = "${seconds / 60}:${(seconds % 60).toString().padStart(2, '0')}"
