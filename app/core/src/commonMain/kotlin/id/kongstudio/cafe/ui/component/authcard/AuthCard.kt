package id.kongstudio.cafe.ui.component.authcard

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.BiasAlignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.window.WidthClass

private val WideFormMaxWidth: Dp = 440.dp
private val NarrowFormMaxWidth: Dp = 520.dp

private val BannerHeight: Dp = 240.dp
private val BannerHeightTiny: Dp = 180.dp

/** Tinggi foto yang tertutup lembar form di layar sempit. */
private val SheetOverlap: Dp = 24.dp

/** Foto toko di satu sisi dan form di sisi lain: berdampingan di layar lebar, foto di atas dan lembar form di bawah di layar sempit. */
@Composable
fun AuthCard(
    brandImage: Painter,
    brandDescription: String,
    modifier: Modifier = Modifier,
    topAction: (@Composable () -> Unit)? = null,
    content: @Composable ColumnScope.(wide: Boolean) -> Unit,
) {
    val colors = AppTheme.colors
    val windowSize = AppTheme.windowSize

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(colors.background),
    ) {
        if (windowSize.isWide) {
            WideLayout(brandImage, brandDescription, content)
        } else {
            NarrowLayout(brandImage, brandDescription, windowSize.width == WidthClass.Tiny, content)
        }

        if (topAction != null) {
            Box(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .safeDrawingPadding()
                    .padding(AppTheme.spacing.sm)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.surface),
            ) { topAction() }
        }
    }
}

@Composable
private fun WideLayout(
    brandImage: Painter,
    brandDescription: String,
    content: @Composable ColumnScope.(wide: Boolean) -> Unit,
) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.card

    Row(modifier = Modifier.fillMaxSize()) {
        Image(
            painter = brandImage,
            contentDescription = brandDescription,
            contentScale = ContentScale.Crop,
            // 30% dari kiri, seperti object-position di web.
            alignment = BiasAlignment(-0.4f, 0f),
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight(),
        )
        BoxWithConstraints(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight()
                .safeDrawingPadding(),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = maxHeight)
                    .verticalScroll(rememberScrollState())
                    .padding(AppTheme.spacing.xxxl),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Column(
                    modifier = Modifier
                        .widthIn(max = WideFormMaxWidth)
                        .fillMaxWidth()
                        .clip(shape)
                        .background(colors.surface)
                        .border(AppTheme.sizes.borderThin, colors.outline, shape)
                        .padding(AppTheme.spacing.xxl + AppTheme.spacing.sm),
                ) {
                    content(true)
                }
            }
        }
    }
}

@Composable
private fun NarrowLayout(
    brandImage: Painter,
    brandDescription: String,
    tiny: Boolean,
    content: @Composable ColumnScope.(wide: Boolean) -> Unit,
) {
    val colors = AppTheme.colors
    val bannerHeight = if (tiny) BannerHeightTiny else BannerHeight

    BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
        val sheetMinHeight = maxHeight - (bannerHeight - SheetOverlap)
        Image(
            painter = brandImage,
            contentDescription = brandDescription,
            contentScale = ContentScale.Crop,
            alignment = BiasAlignment(-0.4f, 0f),
            modifier = Modifier
                .fillMaxWidth()
                .height(bannerHeight),
        )
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(top = bannerHeight - SheetOverlap),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Column(
                modifier = Modifier
                    .widthIn(max = NarrowFormMaxWidth)
                    .fillMaxWidth()
                    .heightIn(min = sheetMinHeight)
                    .clip(AppTheme.shapes.sheet)
                    .background(colors.surface)
                    .navigationBarsPadding()
                    .imePadding()
                    .padding(
                        horizontal = if (tiny) AppTheme.spacing.lg else AppTheme.spacing.xl,
                        vertical = AppTheme.spacing.xl,
                    ),
            ) {
                content(false)
            }
        }
    }
}
