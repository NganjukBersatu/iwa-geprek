package id.kongstudio.cafe.ui.theme

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.poppins_bold
import id.kongstudio.cafe.resources.poppins_medium
import id.kongstudio.cafe.resources.poppins_regular
import id.kongstudio.cafe.resources.poppins_semibold
import org.jetbrains.compose.resources.Font
import id.kongstudio.cafe.ui.theme.color.AppColors
import id.kongstudio.cafe.ui.theme.color.LightAppColors
import id.kongstudio.cafe.ui.theme.effect.AppEffects
import id.kongstudio.cafe.ui.theme.effect.DefaultAppEffects
import id.kongstudio.cafe.ui.theme.shape.AppShapes
import id.kongstudio.cafe.ui.theme.shape.DefaultAppShapes
import id.kongstudio.cafe.ui.theme.size.AppSizes
import id.kongstudio.cafe.ui.theme.size.DefaultAppSizes
import id.kongstudio.cafe.ui.theme.spacing.AppSpacing
import id.kongstudio.cafe.ui.theme.spacing.DefaultAppSpacing
import id.kongstudio.cafe.ui.theme.typography.AppTypography
import id.kongstudio.cafe.ui.theme.typography.DefaultAppTypography
import id.kongstudio.cafe.ui.theme.window.WindowSize

/** Batas pembesaran huruf dari pengaturan sistem; di atasnya tata letak tablet mulai sesak. */
private const val MaxFontScale = 1.15f

private val LocalAppColors = staticCompositionLocalOf { LightAppColors }
private val LocalAppTypography = staticCompositionLocalOf { DefaultAppTypography }
private val LocalAppShapes = staticCompositionLocalOf { DefaultAppShapes }
private val LocalAppSpacing = staticCompositionLocalOf { DefaultAppSpacing }
private val LocalAppSizes = staticCompositionLocalOf { DefaultAppSizes }
private val LocalAppEffects = staticCompositionLocalOf { DefaultAppEffects }
private val LocalWindowSize = staticCompositionLocalOf { WindowSize.Compact }

object AppTheme {
    val colors: AppColors
        @Composable @ReadOnlyComposable get() = LocalAppColors.current

    val typography: AppTypography
        @Composable @ReadOnlyComposable get() = LocalAppTypography.current

    val shapes: AppShapes
        @Composable @ReadOnlyComposable get() = LocalAppShapes.current

    val spacing: AppSpacing
        @Composable @ReadOnlyComposable get() = LocalAppSpacing.current

    val sizes: AppSizes
        @Composable @ReadOnlyComposable get() = LocalAppSizes.current

    val effects: AppEffects
        @Composable @ReadOnlyComposable get() = LocalAppEffects.current

    val windowSize: WindowSize
        @Composable @ReadOnlyComposable get() = LocalWindowSize.current
}

private fun scaledDensity(system: Density, windowSize: WindowSize) =
    Density(density = system.density * windowSize.interfaceScale, fontScale = minOf(system.fontScale, MaxFontScale))

/** Menerapkan skala antarmuka di dalam jendela terpisah (modal), karena jendela itu memulai kepadatan dari pengaturan sistem lagi. */
@Composable
fun AppInterfaceScale(content: @Composable () -> Unit) {
    val system = LocalDensity.current
    val windowSize = LocalWindowSize.current
    val density = remember(system, windowSize) { scaledDensity(system, windowSize) }
    CompositionLocalProvider(LocalDensity provides density, content = content)
}

@Composable
fun AppTheme(content: @Composable () -> Unit) {
    // Poppins sama dengan web manajemen; satu-satunya keluarga huruf teks.
    val poppins = FontFamily(
        Font(Res.font.poppins_regular, FontWeight.Normal),
        Font(Res.font.poppins_medium, FontWeight.Medium),
        Font(Res.font.poppins_semibold, FontWeight.SemiBold),
        Font(Res.font.poppins_bold, FontWeight.Bold),
    )
    val typography = remember(poppins) { DefaultAppTypography.withFontFamily(poppins) }
    BoxWithConstraints(Modifier.fillMaxSize()) {
        val windowSize = WindowSize.from(maxWidth)
        val system = LocalDensity.current
        // Skala layar: layar lebar memperkecil seluruh antarmuka sedikit, dan pembesaran huruf sistem dibatasi supaya tata letak tetap utuh.
        val density = remember(system, windowSize) { scaledDensity(system, windowSize) }
        CompositionLocalProvider(
            LocalDensity provides density,
            LocalAppColors provides LightAppColors,
            LocalAppTypography provides typography,
            LocalAppShapes provides DefaultAppShapes,
            LocalAppSpacing provides DefaultAppSpacing,
            LocalAppSizes provides DefaultAppSizes,
            LocalAppEffects provides DefaultAppEffects,
            LocalWindowSize provides windowSize,
            content = content,
        )
    }
}
