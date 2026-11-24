package id.kongstudio.cafe.ui.component.secondarybutton

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.theme.AppTheme

/** Neutral untuk pendamping biasa, Danger untuk aksi menghapus, Cancel untuk Batal dan Urungkan, berwarna netral sama dengan pendamping biasa (warna aksen hanya hiasan, aturan 6.4). */
enum class ButtonTone { Neutral, Danger, Cancel }

/** Tombol pendamping tombol utama, misalnya batal; [ButtonTone.Danger] untuk tindakan yang membatalkan sesuatu. */
@Composable
fun SecondaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    tone: ButtonTone = ButtonTone.Neutral,
    loading: Boolean = false,
) {
    val colors = AppTheme.colors

    PrimaryButton(
        text = text,
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        loading = loading,
        containerColor = when (tone) {
            ButtonTone.Danger -> colors.dangerContainer
            ButtonTone.Cancel, ButtonTone.Neutral -> colors.selected
        },
        contentColor = when (tone) {
            ButtonTone.Danger -> colors.onDangerContainer
            ButtonTone.Cancel, ButtonTone.Neutral -> colors.primary
        },
    )
}
