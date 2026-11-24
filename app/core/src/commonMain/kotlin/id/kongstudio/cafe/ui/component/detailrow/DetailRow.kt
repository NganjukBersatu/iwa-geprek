package id.kongstudio.cafe.ui.component.detailrow

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pasangan label dan nilai; nilai berupa teks atau konten bebas (misalnya lencana). */
@Composable
fun DetailRow(
    label: String,
    modifier: Modifier = Modifier,
    value: String? = null,
    valueContent: (@Composable () -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier.fillMaxWidth().padding(spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        BasicText(
            text = label,
            style = AppTheme.typography.body.copy(color = colors.contentMuted),
            modifier = Modifier.weight(1f),
        )
        if (valueContent != null) {
            valueContent()
        } else if (value != null) {
            BasicText(
                text = value,
                style = AppTheme.typography.body.copy(color = colors.content, textAlign = TextAlign.End),
                modifier = Modifier.weight(1f),
            )
        }
    }
}
