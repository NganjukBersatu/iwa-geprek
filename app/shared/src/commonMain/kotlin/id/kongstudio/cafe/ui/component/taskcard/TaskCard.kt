package id.kongstudio.cafe.ui.component.taskcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Nuansa kartu per jenis tugas, semuanya dari palet app supaya senada: warna lembut, warna teks, atau warna utama. */
enum class TaskCardTone { Light, Green, Tan }

private class ToneColors(val container: Color, val onContainer: Color, val mutedOnContainer: Color, val check: Color, val badge: BadgeTone)

@Composable
private fun toneColors(tone: TaskCardTone): ToneColors {
    val colors = AppTheme.colors
    return when (tone) {
        TaskCardTone.Light -> ToneColors(colors.selected, colors.primary, colors.contentMuted, colors.primary, BadgeTone.Positive)
        TaskCardTone.Green -> ToneColors(colors.primary, colors.onPrimary, colors.onPrimaryMuted, colors.onPrimarySubtle, BadgeTone.Strong)
        TaskCardTone.Tan -> ToneColors(colors.accentSurface, colors.content, colors.content, colors.primary, BadgeTone.Accent)
    }
}

/**
 * Kartu satu tugas untuk semua jenis: putih selama belum selesai, berwarna [tone] setelah [completed].
 * [tagLabel] dan [icon] menandai jenis atau pemiliknya, [actionLabel] menampilkan tombol aksi, dan [onClick] membuka rinciannya.
 */
@Composable
fun TaskCard(
    title: String,
    tone: TaskCardTone,
    icon: ImageVector,
    completed: Boolean,
    modifier: Modifier = Modifier,
    caption: String? = null,
    note: String? = null,
    tagLabel: String? = null,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
    onClick: (() -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.card
    val toned = toneColors(tone)
    val titleColor = if (completed) toned.onContainer else colors.content
    val mutedColor = if (completed) toned.mutedOnContainer else colors.contentMuted

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(if (completed) toned.container else colors.surface)
            .then(if (completed) Modifier else Modifier.border(AppTheme.sizes.borderThin, colors.divider, shape))
            .then(if (onClick != null) Modifier.clickable(role = Role.Button, onClick = onClick) else Modifier)
            .padding(spacing.lg),
        verticalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            Box(
                modifier = Modifier
                    .size(spacing.compactTarget)
                    .clip(AppTheme.shapes.pill)
                    .background(if (completed) toned.check else toned.container),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(
                    icon = if (completed) AppIcons.Check else icon,
                    tint = if (completed) colors.onPrimary else toned.onContainer,
                    size = AppTheme.sizes.iconSmall,
                )
            }
            Column(modifier = Modifier.weight(1f)) {
                AppText(text = title, role = TextRole.Subtitle, color = titleColor, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (caption != null) AppText(text = caption, role = TextRole.Caption, color = mutedColor, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (note != null) AppText(text = note, role = TextRole.Caption, color = mutedColor)
            }
            if (tagLabel != null && !completed) StatusBadge(text = tagLabel, tone = toned.badge)
        }
        if (actionLabel != null && onAction != null) {
            // Di kartu selesai yang sudah berwarna, tombolnya berlatar permukaan supaya tetap terbaca.
            PrimaryButton(
                text = actionLabel,
                onClick = onAction,
                modifier = Modifier.fillMaxWidth(),
                containerColor = if (completed) colors.surface else toned.container,
                contentColor = if (completed) colors.content else toned.onContainer,
            )
        }
    }
}
