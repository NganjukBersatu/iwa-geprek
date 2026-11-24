package id.kongstudio.cafe.ui.component.featurecard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme

/** Warna latar kartu fitur; semuanya dari palet tema. */
enum class CardTone { Primary, Accent, Soft, Deep }

/** Opasitas lingkaran ikon di atas latar terang. */
private const val BackdropAlpha = 0.45f

/** Opasitas ikon hiasan agar teks di atasnya tetap terbaca. */
private const val DecorationAlpha = 0.13f

/** Ikon hiasan sebagian tinggi kartu, miring dan sebagian sengaja terpotong tepi kanan; semua pecahan dari tinggi kartu. */
private const val DecorationSizeFraction = 0.78f
private const val DecorationOffsetXFraction = 0.14f
private const val DecorationOffsetYFraction = 0.06f
private const val DecorationTilt = -12f

/** Kartu lebih pendek dari sekian kali tinggi badge memakai susunan berdampingan. */
private const val CompactHeightFactor = 2.2f

/** Kartu satu fitur: badge ikon di atas, judul di bawah, hiasan ikon di latar; seluruh kartu dapat disentuh. */
@Composable
fun FeatureCard(
    title: String,
    icon: ImageVector,
    decoration: ImageVector,
    tone: CardTone,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val dark = tone == CardTone.Primary || tone == CardTone.Deep
    val container = when (tone) {
        CardTone.Primary -> colors.primary
        CardTone.Accent -> colors.accent
        CardTone.Soft -> colors.surfaceAccent
        CardTone.Deep -> colors.content
    }
    val content = if (dark) colors.onPrimary else colors.content
    val backdrop = if (dark) colors.onPrimarySubtle else colors.surface.copy(alpha = BackdropAlpha)

    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .clip(AppTheme.shapes.card)
            .background(container)
            .clickable(role = Role.Button, onClick = onClick),
    ) {
        AppIcon(
            icon = decoration,
            tint = content.copy(alpha = DecorationAlpha),
            size = maxHeight * DecorationSizeFraction,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .offset(x = maxHeight * DecorationOffsetXFraction, y = maxHeight * DecorationOffsetYFraction)
                .rotate(DecorationTilt),
        )
        val spacing = AppTheme.spacing
        val badge: @Composable () -> Unit = {
            Box(
                modifier = Modifier
                    .size(AppTheme.sizes.control)
                    .clip(AppTheme.shapes.pill)
                    .background(backdrop),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(icon = icon, tint = content, size = AppTheme.sizes.icon)
            }
        }
        // Kartu pendek: badge dan judul berdampingan karena susunan atas-bawah tidak muat.
        val compact = maxHeight < AppTheme.sizes.control * CompactHeightFactor + spacing.md * 2

        if (compact) {
            Row(
                modifier = Modifier.fillMaxSize().padding(horizontal = spacing.md),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                badge()
                AppText(text = title, role = TextRole.Subtitle, color = content)
            }
        } else {
            Column(
                modifier = Modifier.fillMaxSize().padding(spacing.md),
                verticalArrangement = Arrangement.SpaceBetween,
            ) {
                badge()
                AppText(text = title, role = TextRole.Subtitle, color = content)
            }
        }
    }
}
