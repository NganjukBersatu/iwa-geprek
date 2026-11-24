package id.kongstudio.cafe.ui.component.inlinemessage

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.ui.theme.AppTheme

enum class MessageTone { Error, Success }

@Composable
fun InlineMessage(
    text: String,
    modifier: Modifier = Modifier,
    tone: MessageTone = MessageTone.Error,
) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.field
    val container = if (tone == MessageTone.Error) colors.dangerContainer else colors.selected
    val content = if (tone == MessageTone.Error) colors.onDangerContainer else colors.primary
    val border = if (tone == MessageTone.Error) colors.danger else colors.outline

    BasicText(
        text = text,
        style = AppTheme.typography.caption.copy(color = content),
        modifier = modifier
            .fillMaxWidth()
            .semantics { liveRegion = LiveRegionMode.Polite }
            .clip(shape)
            .background(container)
            .border(AppTheme.sizes.borderThin, border, shape)
            .padding(horizontal = AppTheme.spacing.md, vertical = AppTheme.spacing.sm),
    )
}
