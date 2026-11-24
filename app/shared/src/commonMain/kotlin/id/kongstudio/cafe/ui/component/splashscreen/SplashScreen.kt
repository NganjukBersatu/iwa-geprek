package id.kongstudio.cafe.ui.component.splashscreen

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.splash_app_name
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.delay
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

private const val LogoWidthFraction = 0.4f
private const val LogoHeightFraction = 0.35f
private const val LogoRotateFromDegrees = -25f
private const val StartDelayMillis = 250L
private const val LogoMillis = 750
private const val NameMillis = 450
private const val HoldMillis = 1_300L
private const val ExitMillis = 850
private const val ExitOvershoot = 1.02f
private const val ContentScaleFrom = 1.1f
private const val ContentDimFrom = 0.3f
private val NameRise = 12.dp
private val ExitCornerRadius = 60.dp

/** Layar pembuka: logo memantul masuk, nama naik, lalu layar terangkat membuka [content], yang baru disusun saat [ready] benar. */
@Composable
fun SplashScreen(
    ready: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val effects = AppTheme.effects
    val logo = remember { Animatable(0f) }
    val name = remember { Animatable(0f) }
    val exit = remember { Animatable(0f) }
    var introDone by remember { mutableStateOf(false) }
    var finished by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        delay(StartDelayMillis)
        logo.animateTo(1f, tween(LogoMillis, easing = effects.bounce))
        name.animateTo(1f, tween(NameMillis))
        delay(HoldMillis)
        introDone = true
    }
    LaunchedEffect(ready, introDone) {
        if (ready && introDone) {
            exit.animateTo(1f, tween(ExitMillis, easing = effects.exit))
            finished = true
        }
    }

    Box(modifier.fillMaxSize()) {
        if (ready) {
            Box(
                Modifier.fillMaxSize().graphicsLayer {
                    val scale = ContentScaleFrom - (ContentScaleFrom - 1f) * exit.value
                    scaleX = scale
                    scaleY = scale
                },
            ) { content() }
            if (!finished) {
                Box(
                    Modifier.fillMaxSize()
                        .background(AppTheme.colors.scrim.copy(alpha = ContentDimFrom * (1f - exit.value))),
                )
            }
        }
        if (!finished) SplashPage(logo = logo.value, name = name.value, exit = exit.value)
    }
}

@Composable
private fun SplashPage(logo: Float, name: Float, exit: Float) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val description = stringResource(Res.string.common_loading)

    BoxWithConstraints(
        modifier = Modifier
            .fillMaxSize()
            .graphicsLayer { translationY = -size.height * ExitOvershoot * exit }
            .clip(RoundedCornerShape(bottomStart = ExitCornerRadius * exit, bottomEnd = ExitCornerRadius * exit))
            .background(colors.primary)
            .semantics {
                contentDescription = description
                liveRegion = LiveRegionMode.Polite
            },
        contentAlignment = Alignment.Center,
    ) {
        // Ukuran logo dibatasi lebar dan tinggi layar supaya tidak meluber di ponsel landscape.
        val logoSize = minOf(maxWidth * LogoWidthFraction, maxHeight * LogoHeightFraction, AppTheme.sizes.sidePanelWidth)
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(spacing.lg),
            modifier = Modifier.fillMaxWidth().padding(horizontal = spacing.xl),
        ) {
            Image(
                painter = painterResource(Res.drawable.brand_logo),
                contentDescription = null,
                modifier = Modifier
                    .size(logoSize)
                    .graphicsLayer {
                        scaleX = logo
                        scaleY = logo
                        rotationZ = LogoRotateFromDegrees * (1f - logo)
                    },
            )
            BasicText(
                text = stringResource(Res.string.splash_app_name),
                style = AppTheme.typography.headline.copy(color = colors.onPrimary, textAlign = TextAlign.Center),
                modifier = Modifier.graphicsLayer {
                    alpha = name
                    translationY = NameRise.toPx() * (1f - name)
                },
            )
        }
    }
}
