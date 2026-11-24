package id.kongstudio.cafe.ui.component.profileheader

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.imagepreview.ImagePreviewDialog
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private val AvatarSize = 116.dp
private val CameraBadgeSize = 38.dp
private val CameraBadgeBorder = 3.dp
private val DecorationSize = 170.dp
private val DecorationOffsetX = 28.dp
private val DecorationOffsetY = 14.dp
private const val DecorationAlpha = 0.13f
private const val DecorationTilt = -12f

/**
 * Kepala halaman Profil: avatar yang membuka pratinjau foto dan lencana kamera untuk ganti foto,
 * nama, serta label peran dan cabang dengan tombol keluar di ujung baris label.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ProfileHeader(
    name: String,
    labels: List<String>,
    photoUrl: String?,
    logoutLabel: String,
    changePhotoLabel: String,
    onLogout: () -> Unit,
    onChangePhoto: (() -> Unit)?,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var previewUrl by remember { mutableStateOf<String?>(null) }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(AppTheme.shapes.card)
            .background(colors.surfaceAccent),
    ) {
        AppIcon(
            icon = AppIcons.UserCircle,
            tint = colors.content.copy(alpha = DecorationAlpha),
            size = DecorationSize,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .offset(x = DecorationOffsetX, y = DecorationOffsetY)
                .rotate(DecorationTilt),
        )
        Row(
            modifier = Modifier.padding(spacing.lg),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.lg),
        ) {
            Avatar(
                photoUrl = photoUrl,
                changePhotoLabel = changePhotoLabel,
                onPreview = { previewUrl = it },
                onChangePhoto = onChangePhoto,
            )
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                AppText(
                    text = name,
                    role = TextRole.Title,
                    color = colors.content,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                    verticalArrangement = Arrangement.spacedBy(spacing.sm),
                ) {
                    labels.forEach { Label(it) }
                }
                LogoutButton(label = logoutLabel, onClick = onLogout)
            }
        }
    }

    previewUrl?.let { url -> ImagePreviewDialog(url = url, onDismiss = { previewUrl = null }) }
}

@Composable
private fun LogoutButton(label: String, onClick: () -> Unit) {
    val colors = AppTheme.colors

    Row(
        modifier = Modifier
            .clip(AppTheme.shapes.pill)
            .background(colors.danger)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = AppTheme.spacing.md, vertical = AppTheme.spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        AppIcon(
            icon = AppIcons.Logout,
            tint = colors.onPrimary,
            size = AppTheme.sizes.iconSmall,
        )
        AppText(text = label, role = TextRole.Label, color = colors.onPrimary)
    }
}

@Composable
private fun Label(text: String) {
    val colors = AppTheme.colors

    AppText(
        text = text,
        role = TextRole.Label,
        color = colors.content,
        modifier = Modifier
            .clip(AppTheme.shapes.pill)
            .background(colors.surface)
            .padding(horizontal = AppTheme.spacing.md, vertical = AppTheme.spacing.xs),
    )
}

@Composable
private fun Avatar(
    photoUrl: String?,
    changePhotoLabel: String,
    onPreview: (String) -> Unit,
    onChangePhoto: (() -> Unit)?,
) {
    val colors = AppTheme.colors
    // Tanpa foto tidak ada yang bisa dipratinjau, jadi ketukan avatar langsung membuka ganti foto.
    val action = when {
        photoUrl != null -> Modifier.clickable(role = Role.Button, onClick = { onPreview(photoUrl) })
        onChangePhoto != null -> Modifier.clickable(onClickLabel = changePhotoLabel, role = Role.Button, onClick = onChangePhoto)
        else -> Modifier
    }

    Box(modifier = Modifier.size(AvatarSize)) {
        Box(
            modifier = Modifier
                .size(AvatarSize)
                .clip(AppTheme.shapes.pill)
                .background(colors.primary)
                .then(action),
            contentAlignment = Alignment.Center,
        ) {
            if (photoUrl != null) {
                AsyncImage(
                    model = photoUrl,
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.matchParentSize(),
                )
            } else {
                AppIcon(icon = AppIcons.UserCircle, tint = colors.onPrimary, size = AppTheme.sizes.iconXLarge)
            }
        }
        if (onChangePhoto != null) {
            Box(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .size(CameraBadgeSize)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.accentSurface)
                    .border(CameraBadgeBorder, colors.surfaceAccent, AppTheme.shapes.pill)
                    .clickable(onClickLabel = changePhotoLabel, role = Role.Button, onClick = onChangePhoto),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(
                    icon = AppIcons.Camera,
                    tint = colors.content,
                    size = AppTheme.sizes.iconSmall,
                    contentDescription = changePhotoLabel,
                )
            }
        }
    }
}
