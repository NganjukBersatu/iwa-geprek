package id.kongstudio.cafe.ui.component.bottomsheet

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutLinearInEasing
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.sheet_close
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.progressline.ProgressLine
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.launch
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.component.appicon.AppIcon

private const val SheetMaxHeightFraction = 0.9f
private const val EnterDurationMs = 280
private const val ExitDurationMs = 200

/** Panel modal dari tepi bawah yang ditutup dengan ketuk di luar, tombol tutup, atau tombol kembali, kecuali [dismissible] false. */
@Composable
fun AppBottomSheet(
    title: String,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    dismissible: Boolean = true,
    visible: Boolean = true,
    /** Diisi pemanggil yang perlu tahu posisi gulir, misalnya untuk memuat halaman berikutnya. */
    scroll: ScrollState = rememberScrollState(),
    /** Garis progres di bawah judul selama isi lembar sedang dimuat. */
    busy: Boolean = false,
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
        BoxWithConstraints(
            modifier = Modifier
                .fillMaxSize()
                // Lembar naik di atas papan ketik, sehingga isian dan tombolnya tidak tertutup.
                .imePadding()
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    onClick = { if (dismissible) close() },
                ),
            contentAlignment = Alignment.BottomCenter,
        ) {
            Column(
                modifier = modifier
                    .widthIn(max = AppTheme.sizes.contentMaxWidth)
                    .fillMaxWidth()
                    .heightIn(max = maxHeight * SheetMaxHeightFraction)
                    .graphicsLayer { translationY = (1f - progress.value) * size.height }
                    .clip(AppTheme.shapes.sheet)
                    .background(colors.background)
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                        onClick = {},
                    ),
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = spacing.lg),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    BasicText(
                        text = title,
                        style = AppTheme.typography.title.copy(color = colors.content),
                        modifier = Modifier.weight(1f),
                    )
                    if (dismissible) {
                        Box(
                            modifier = Modifier
                                .size(spacing.touchTarget)
                                .clickable(role = Role.Button, onClick = ::close),
                            contentAlignment = Alignment.Center,
                        ) {
                            AppIcon(icon = AppIcons.Close, tint = colors.content, size = AppTheme.sizes.icon, contentDescription = stringResource(Res.string.sheet_close))
                        }
                    } else {
                        Box(modifier = Modifier.size(spacing.touchTarget))
                    }
                }
                AppDivider()
                // Garis ditumpuk di atas isi, supaya muncul dan hilangnya tidak menggeser isi lembar.
                Box {
                    Column(
                        modifier = Modifier
                            .verticalScroll(scroll)
                            .windowInsetsPadding(WindowInsets.navigationBars)
                            .padding(spacing.lg),
                        // Jarak antarbagian isi diatur di sini, supaya setiap lembar berjarak sama tanpa menyusun Column sendiri.
                        verticalArrangement = Arrangement.spacedBy(spacing.md),
                        content = content,
                    )
                    if (busy) ProgressLine(modifier = Modifier.align(Alignment.TopCenter))
                }
            }
        }
    }
}
