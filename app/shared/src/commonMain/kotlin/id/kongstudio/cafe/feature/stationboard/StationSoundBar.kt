package id.kongstudio.cafe.feature.stationboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.station_mute_five
import id.kongstudio.cafe.resources.station_muted_left
import id.kongstudio.cafe.resources.station_unmute
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.toggleswitch.ToggleSwitch
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.delay
import org.jetbrains.compose.resources.stringResource

private val ActionButtonWidth = 200.dp
private const val MillisPerSecond = 1_000L

/**
 * Kendali bunyi di kepala papan: saklar, lalu tombol bisukan sementara atau, selama dibisukan, sisa waktunya beserta tombol aktifkan.
 * Di layar lebar sebaris selebar isinya di samping judul; di layar sempit bertumpuk di bawah judul, tombol selebar baris.
 */
@Composable
internal fun StationSoundBar(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    mutedUntil: Long,
    onMute: () -> Unit,
    onUnmute: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val muted = mutedUntil != 0L
    var now by remember(mutedUntil) { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(mutedUntil) {
        if (!muted) return@LaunchedEffect
        while (true) {
            now = ServerClock.nowEpochSeconds()
            delay(MillisPerSecond)
        }
    }
    val left = (mutedUntil - now).coerceAtLeast(0L)
    val leftText = "${(left / 60L).toString().padStart(2, '0')}:${(left % 60L).toString().padStart(2, '0')}"

    val action: @Composable (Modifier) -> Unit = { buttonModifier ->
        SecondaryButton(
            text = stringResource(if (muted) Res.string.station_unmute else Res.string.station_mute_five),
            onClick = if (muted) onUnmute else onMute,
            modifier = buttonModifier,
        )
    }
    val toggle: @Composable (Modifier) -> Unit = { toggleModifier ->
        ToggleSwitch(label = label, checked = checked, onCheckedChange = onCheckedChange, modifier = toggleModifier)
    }
    val status: @Composable () -> Unit = {
        if (muted) {
            AppText(text = stringResource(Res.string.station_muted_left, leftText), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
        }
    }

    if (AppTheme.windowSize.isWide) {
        Row(
            modifier = modifier,
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            toggle(Modifier)
            status()
            action(Modifier.width(ActionButtonWidth))
        }
    } else {
        Column(modifier = modifier.fillMaxWidth().padding(top = spacing.xs), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
            toggle(Modifier.fillMaxWidth())
            status()
            action(Modifier)
        }
    }
}
