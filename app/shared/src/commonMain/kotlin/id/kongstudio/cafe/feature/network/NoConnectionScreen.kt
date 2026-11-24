package id.kongstudio.cafe.feature.network

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.network_lost_message
import id.kongstudio.cafe.resources.network_lost_title
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.backhandler.PlatformBackHandler
import id.kongstudio.cafe.ui.component.cryinglogo.CryingLogo
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

/** Halaman layar penuh saat internet putus; menahan sentuhan dan tombol kembali agar layar di bawahnya tidak berubah. */
@Composable
internal fun NoConnectionScreen(modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    PlatformBackHandler(enabled = true, onBack = {})

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(colors.background)
            .clickable(interactionSource = remember { MutableInteractionSource() }, indication = null, onClick = {})
            .padding(horizontal = spacing.xl),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(spacing.lg, Alignment.CenterVertically),
    ) {
        CryingLogo(painter = painterResource(Res.drawable.brand_logo), badgeIcon = AppIcons.WifiOff)
        AppText(
            text = stringResource(Res.string.network_lost_title),
            role = TextRole.Headline,
            color = colors.content,
            textAlign = TextAlign.Center,
        )
        AppText(
            text = stringResource(Res.string.network_lost_message),
            role = TextRole.Body,
            color = colors.contentMuted,
            textAlign = TextAlign.Center,
        )
    }
}
