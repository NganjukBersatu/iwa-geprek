package id.kongstudio.cafe.ui.component.shiftrow

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.codebadge.CodeBadge
import id.kongstudio.cafe.ui.component.listrow.ListRow
import id.kongstudio.cafe.ui.theme.AppTheme

/** Baris satu penugasan shift: judul, keterangan, lencana kode berwarna, dan penanda opsional. */
@Composable
fun ShiftRow(
    title: String,
    modifier: Modifier = Modifier,
    detail: String? = null,
    caption: String? = null,
    footnote: String? = null,
    code: String? = null,
    codeColor: Color? = null,
    tag: String? = null,
) {
    ListRow(
        title = title,
        detail = detail,
        caption = caption,
        footnote = footnote,
        modifier = modifier,
        trailing = {
            if (tag != null || code != null) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
                ) {
                    if (tag != null) StatusBadge(text = tag, tone = BadgeTone.Positive)
                    if (code != null) CodeBadge(text = code, color = codeColor)
                }
            }
        },
    )
}
