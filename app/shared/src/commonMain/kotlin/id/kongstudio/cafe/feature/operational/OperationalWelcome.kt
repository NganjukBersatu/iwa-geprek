package id.kongstudio.cafe.feature.operational

import id.kongstudio.cafe.ui.component.screenbackdrop.ScreenBackdrop
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.successstate.SuccessState
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.StringArrayResource
import org.jetbrains.compose.resources.stringArrayResource
import kotlin.random.Random

/** Layar sesaat saat karyawan masuk (sambutan) atau keluar (salam keluar); satu kalimat dari [messages] dipilih acak tiap kali tampil. */
@Composable
internal fun OperationalWelcome(
    userName: String?,
    messages: StringArrayResource,
    icon: ImageVector,
    modifier: Modifier = Modifier,
) {
    val lines = stringArrayResource(messages)
    val pick = remember { Random.nextInt(Int.MAX_VALUE) }
    ScreenBackdrop(modifier = modifier, contentAlignment = Alignment.Center) {
        SuccessState(
            title = greetingText(userName),
            message = lines.getOrNull(pick % lines.size.coerceAtLeast(1)).orEmpty(),
            icon = icon,
            modifier = Modifier.padding(horizontal = AppTheme.windowSize.pagePadding),
        )
    }
}
