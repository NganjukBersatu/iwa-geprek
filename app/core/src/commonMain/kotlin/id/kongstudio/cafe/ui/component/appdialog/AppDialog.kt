package id.kongstudio.cafe.ui.component.appdialog

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutLinearInEasing
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sheet_close
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppInterfaceScale
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource

private const val DialogMaxHeightFraction = 0.94f
private const val EnterScale = 0.95f
private const val EnterDurationMs = 220
private const val ExitDurationMs = 160

/** Lebar modal yang lazim: [Narrow] untuk satu kolom, [Wide] untuk dua kolom berdampingan. */
object AppDialogWidth {
    val Narrow: Dp = 448.dp
    val Wide: Dp = 896.dp
}

/** Modal tengah berkepala warna utama dengan [title] dan tombol tutup yang juga tertutup lewat ketuk luar atau tombol kembali kecuali [dismissible] false (pemanggil menutupnya lewat [visible] false), sedangkan [content] mengatur gulirnya sendiri. */
@Composable
fun AppDialog(
    title: String,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    maxWidth: Dp = AppDialogWidth.Narrow,
    dismissible: Boolean = true,
    visible: Boolean = true,
    content: @Composable ColumnScope.() -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val progress = remember { Animatable(0f) }
    val scope = rememberCoroutineScope()
    var closing by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        progress.animateTo(1f, tween(EnterDurationMs, easing = FastOutSlowInEasing))
    }

    fun close() {
        if (closing) return
        closing = true
        scope.launch {
            progress.animateTo(0f, tween(ExitDurationMs, easing = FastOutLinearInEasing))
            onDismiss()
        }
    }

    LaunchedEffect(visible) { if (!visible) close() }

    Dialog(
        onDismissRequest = { if (dismissible) close() },
        properties = DialogProperties(
            dismissOnBackPress = dismissible,
            dismissOnClickOutside = dismissible,
            usePlatformDefaultWidth = false,
        ),
    ) {
        AppInterfaceScale {
            BoxWithConstraints(
                modifier = Modifier
                    .fillMaxSize()
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                        onClick = { if (dismissible) close() },
                    )
                    .imePadding()
                    .padding(spacing.sm),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    modifier = modifier
                        .widthIn(max = maxWidth)
                        .fillMaxWidth()
                        .heightIn(max = maxHeight * DialogMaxHeightFraction)
                        .graphicsLayer {
                            alpha = progress.value
                            val scale = EnterScale + (1f - EnterScale) * progress.value
                            scaleX = scale
                            scaleY = scale
                        }
                        .clip(AppTheme.shapes.dialog)
                        .background(colors.surface)
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null,
                            onClick = {},
                        ),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(colors.primary)
                            .padding(start = spacing.lg),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        BasicText(
                            text = title,
                            style = AppTheme.typography.subtitle.copy(color = colors.onPrimary),
                            modifier = Modifier.weight(1f).padding(vertical = spacing.sm),
                        )
                        Box(
                            modifier = Modifier
                                .size(spacing.touchTarget)
                                .clickable(enabled = dismissible, role = Role.Button, onClick = ::close),
                            contentAlignment = Alignment.Center,
                        ) {
                            if (dismissible) {
                                AppIcon(
                                    icon = AppIcons.Close,
                                    tint = colors.onPrimary,
                                    size = AppTheme.sizes.iconSmall,
                                    contentDescription = stringResource(Res.string.sheet_close),
                                )
                            }
                        }
                    }
                    content()
                }
            }
        }
    }
}
