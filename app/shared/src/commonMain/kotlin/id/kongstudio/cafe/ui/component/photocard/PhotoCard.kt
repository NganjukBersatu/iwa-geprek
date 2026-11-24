package id.kongstudio.cafe.ui.component.photocard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.remoteimage.RemoteImage
import id.kongstudio.cafe.ui.theme.AppTheme

/** Foto dengan keterangan di bawahnya; ketuk untuk membuka pratinjau. */
@Composable
fun PhotoCard(
    url: String,
    caption: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.clickable(role = Role.Button, onClick = onClick),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        RemoteImage(url = url, contentDescription = caption)
        BasicText(
            text = caption,
            style = AppTheme.typography.caption.copy(color = AppTheme.colors.contentMuted),
        )
    }
}
