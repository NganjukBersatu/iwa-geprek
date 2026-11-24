package id.kongstudio.cafe.ui.component.initialsavatar

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.ui.theme.AppTheme

private const val MaxInitials = 2

/** Huruf awal paling banyak dua kata pertama dari [name], huruf besar; kosong bila nama kosong. */
fun initialsOf(name: String): String =
    name.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }.take(MaxInitials)
        .joinToString("") { it.first().uppercase() }

/** Avatar bulat berisi inisial orang, dipakai bila foto tidak ada. */
@Composable
fun InitialsAvatar(name: String, modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    Box(
        modifier = modifier
            .size(AppTheme.sizes.controlSmall)
            .clip(AppTheme.shapes.pill)
            .background(colors.selected),
        contentAlignment = Alignment.Center,
    ) {
        BasicText(text = initialsOf(name), style = AppTheme.typography.label.copy(color = colors.primary))
    }
}
