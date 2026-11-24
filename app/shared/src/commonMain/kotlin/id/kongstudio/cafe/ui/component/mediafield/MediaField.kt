package id.kongstudio.cafe.ui.component.mediafield

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.media_limit_reached
import id.kongstudio.cafe.resources.media_take_photo
import id.kongstudio.cafe.resources.media_video_record
import id.kongstudio.cafe.resources.media_video_too_large
import id.kongstudio.cafe.resources.photo_camera
import id.kongstudio.cafe.resources.photo_gallery
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.mediagallerypicker.rememberMediaGalleryPicker
import id.kongstudio.cafe.ui.component.mediatile.MediaTile
import id.kongstudio.cafe.ui.component.photopicker.rememberPhotoPicker
import id.kongstudio.cafe.ui.component.sourcebutton.SourceButton
import id.kongstudio.cafe.ui.component.videopicker.PickedVideo
import id.kongstudio.cafe.ui.component.videopicker.rememberVideoPicker
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.decodeToImageBitmap
import org.jetbrains.compose.resources.stringResource

enum class MediaKind { Photo, Video }

/** Satu foto atau video yang baru dipilih dan belum diunggah. */
class PickedMedia(val kind: MediaKind, val bytes: ByteArray, val mimeType: String, val fileName: String)

const val MaxPhotos = 5
const val MaxVideos = 1

private const val PhotoMime = "image/jpeg"
private const val PhotoName = "foto.jpg"
private const val VideoNamePrefix = "video"

/** Kolom lampiran: deretan pratinjau yang bisa dihapus, lalu tombol Kamera (foto atau video) dan Galeri (foto dan video sekaligus); [existingPhotos] dan [existingVideos] memperhitungkan lampiran yang sudah tersimpan. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MediaField(
    items: List<PickedMedia>,
    onChange: (List<PickedMedia>) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    existingPhotos: Int = 0,
    existingVideos: Int = 0,
) {
    val spacing = AppTheme.spacing
    val latest by rememberUpdatedState(items)
    var tooLarge by remember { mutableStateOf(false) }

    var choosingCamera by remember { mutableStateOf(false) }
    var limitReached by remember { mutableStateOf(false) }

    fun hasRoom(kind: MediaKind): Boolean = when (kind) {
        MediaKind.Photo -> existingPhotos + latest.count { it.kind == kind } < MaxPhotos
        MediaKind.Video -> existingVideos + latest.count { it.kind == kind } < MaxVideos
    }

    // Satu pintu penambahan: lampiran melewati batas ditolak dengan pesan, bukan hilang diam-diam.
    fun add(media: PickedMedia) {
        tooLarge = false
        limitReached = !hasRoom(media.kind)
        if (!limitReached) onChange(latest + media)
    }

    val photoPicker = rememberPhotoPicker { photo -> add(PickedMedia(MediaKind.Photo, photo.bytes, PhotoMime, PhotoName)) }
    val videoPicker = rememberVideoPicker(onPicked = { video -> add(video.toMedia()) }, onTooLarge = { tooLarge = true })
    val galleryPicker = rememberMediaGalleryPicker(
        onPhoto = { photo -> add(PickedMedia(MediaKind.Photo, photo.bytes, PhotoMime, PhotoName)) },
        onVideo = { video -> add(video.toMedia()) },
        onTooLarge = { tooLarge = true },
    )

    val canAddPhoto = enabled && existingPhotos + items.count { it.kind == MediaKind.Photo } < MaxPhotos
    val canAddVideo = enabled && existingVideos + items.count { it.kind == MediaKind.Video } < MaxVideos

    if (choosingCamera) {
        AppBottomSheet(title = stringResource(Res.string.photo_camera), onDismiss = { choosingCamera = false }) {
            Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
                SourceButton(
                    label = stringResource(Res.string.media_take_photo),
                    icon = AppIcons.Camera,
                    onClick = {
                        choosingCamera = false
                        photoPicker.takePhoto()
                    },
                    enabled = canAddPhoto,
                    modifier = Modifier.weight(1f),
                )
                SourceButton(
                    label = stringResource(Res.string.media_video_record),
                    icon = AppIcons.Video,
                    onClick = {
                        choosingCamera = false
                        videoPicker.record()
                    },
                    enabled = canAddVideo,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
        if (items.isNotEmpty()) {
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                verticalArrangement = Arrangement.spacedBy(spacing.sm),
            ) {
                items.forEach { item ->
                    Thumbnail(item = item, enabled = enabled, onRemove = { onChange(items - item) })
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(spacing.sm)) {
            SourceButton(
                label = stringResource(Res.string.photo_camera),
                icon = AppIcons.Camera,
                onClick = { choosingCamera = true },
                enabled = canAddPhoto || canAddVideo,
                modifier = Modifier.weight(1f),
            )
            SourceButton(
                label = stringResource(Res.string.photo_gallery),
                icon = AppIcons.Photo,
                onClick = galleryPicker::pick,
                enabled = canAddPhoto || canAddVideo,
                modifier = Modifier.weight(1f),
            )
        }
        if (tooLarge) InlineMessage(text = stringResource(Res.string.media_video_too_large))
        if (limitReached) InlineMessage(text = stringResource(Res.string.media_limit_reached))
    }
}

private fun PickedVideo.toMedia() = PickedMedia(
    kind = MediaKind.Video,
    bytes = bytes,
    mimeType = when (extension) {
        ".mov" -> "video/quicktime"
        ".webm" -> "video/webm"
        else -> "video/mp4"
    },
    fileName = VideoNamePrefix + extension,
)

@Composable
private fun Thumbnail(item: PickedMedia, enabled: Boolean, onRemove: () -> Unit) {
    MediaTile(onRemove = onRemove, removeEnabled = enabled) {
        if (item.kind == MediaKind.Photo) {
            val bitmap = remember(item) { item.bytes.decodeToImageBitmap() }
            Image(
                bitmap = bitmap,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.matchParentSize(),
            )
        } else {
            AppIcon(icon = AppIcons.Video, tint = AppTheme.colors.primary, size = AppTheme.sizes.iconLarge)
        }
    }
}
