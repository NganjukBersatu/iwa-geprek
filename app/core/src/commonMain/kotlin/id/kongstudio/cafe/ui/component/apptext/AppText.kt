package id.kongstudio.cafe.ui.component.apptext

import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import id.kongstudio.cafe.ui.theme.AppTheme

/** Peran teks yang memilih gaya dari token tipografi, supaya halaman tidak menulis gaya sendiri. */
enum class TextRole { Display, Headline, Title, Section, Subtitle, Body, Label, Caption }

/** Satu-satunya cara halaman menampilkan teks: [role] memilih gaya dan [color] dari warna tema. */
@Composable
fun AppText(
    text: String,
    modifier: Modifier = Modifier,
    role: TextRole = TextRole.Body,
    color: Color = AppTheme.colors.content,
    textAlign: TextAlign? = null,
    maxLines: Int = Int.MAX_VALUE,
    overflow: TextOverflow = TextOverflow.Clip,
) {
    val typography = AppTheme.typography
    val base = when (role) {
        TextRole.Display -> typography.display
        TextRole.Headline -> typography.headline
        TextRole.Title -> typography.title
        TextRole.Section -> typography.section
        TextRole.Subtitle -> typography.subtitle
        TextRole.Body -> typography.body
        TextRole.Label -> typography.label
        TextRole.Caption -> typography.caption
    }
    BasicText(
        text = text,
        modifier = modifier,
        style = base.copy(color = color, textAlign = textAlign ?: base.textAlign),
        maxLines = maxLines,
        overflow = overflow,
    )
}
