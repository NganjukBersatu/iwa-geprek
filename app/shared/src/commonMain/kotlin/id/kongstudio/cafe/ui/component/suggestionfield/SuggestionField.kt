package id.kongstudio.cafe.ui.component.suggestionfield

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private val ListMaxHeight = 224.dp

/** Satu saran: [title] dipakai juga untuk inisial di lingkaran kiri, [trailing] keterangan pendek di kanan. */
internal class Suggestion(val key: String, val title: String, val subtitle: String? = null, val trailing: String? = null)

/** Kolom teks bebas dengan daftar saran selama difokus yang memanggil [onPick], dan [linked] menandai isian yang tertaut ke saran dengan centang di ujung kolom. */
@Composable
internal fun SuggestionField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    suggestions: List<Suggestion>,
    onPick: (Suggestion) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    linked: Boolean = false,
    linkedDescription: String? = null,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    var focused by remember { mutableStateOf(false) }

    Column(
        modifier = modifier.onFocusChanged { focused = it.hasFocus },
        verticalArrangement = Arrangement.spacedBy(spacing.xs),
    ) {
        AppTextField(
            value = value,
            onValueChange = onValueChange,
            label = label,
            placeholder = placeholder,
            keyboardOptions = keyboardOptions,
            keyboardActions = keyboardActions,
            trailing = if (linked) {
                {
                    AppIcon(
                        icon = AppIcons.UserCheck,
                        tint = colors.primary,
                        size = AppTheme.sizes.iconSmall,
                        contentDescription = linkedDescription,
                        modifier = Modifier.padding(end = spacing.md),
                    )
                }
            } else {
                null
            },
        )
        if (focused && suggestions.isNotEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = ListMaxHeight)
                    .clip(AppTheme.shapes.field)
                    .background(colors.surface)
                    .border(AppTheme.sizes.borderThin, colors.divider, AppTheme.shapes.field)
                    .verticalScroll(rememberScrollState()),
            ) {
                suggestions.forEach { suggestion -> SuggestionRow(suggestion, onClick = { onPick(suggestion) }) }
            }
        }
    }
}

@Composable
private fun SuggestionRow(suggestion: Suggestion, onClick: () -> Unit) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val typography = AppTheme.typography

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = spacing.touchTarget)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.md, vertical = spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        Box(
            modifier = Modifier.size(AppTheme.sizes.avatarSmall).clip(CircleShape).background(colors.selected),
            contentAlignment = Alignment.Center,
        ) {
            BasicText(
                text = suggestion.title.take(1).uppercase(),
                style = typography.label.copy(color = colors.primary),
            )
        }
        Column(modifier = Modifier.weight(1f)) {
            BasicText(
                text = suggestion.title,
                style = typography.body.copy(color = colors.content),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            suggestion.subtitle?.let {
                BasicText(
                    text = it,
                    style = typography.caption.copy(color = colors.contentMuted),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
        suggestion.trailing?.let {
            BasicText(text = it, style = typography.caption.copy(color = colors.contentMuted))
        }
    }
}
