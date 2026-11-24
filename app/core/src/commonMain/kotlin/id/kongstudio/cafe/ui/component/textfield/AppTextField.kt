package id.kongstudio.cafe.ui.component.textfield

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.foundation.text.BasicText
import id.kongstudio.cafe.ui.theme.AppTheme

@Composable
fun AppTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    enabled: Boolean = true,
    isError: Boolean = false,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    trailing: (@Composable () -> Unit)? = null,
    labelColor: Color = AppTheme.colors.content,
    focusColor: Color = AppTheme.colors.primary,
) {
    val colors = AppTheme.colors
    val typography = AppTheme.typography
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    var focused by remember { mutableStateOf(false) }

    val borderColor = when {
        isError -> colors.danger
        focused -> focusColor
        else -> colors.outline
    }
    val borderWidth = if (focused || isError) AppTheme.sizes.borderThick else AppTheme.sizes.borderField

    Column(modifier) {
        BasicText(
            text = label,
            style = typography.label.copy(color = labelColor),
        )
        Spacer(Modifier.height(spacing.xs))
        BasicTextField(
            value = value,
            onValueChange = onValueChange,
            enabled = enabled,
            singleLine = true,
            textStyle = typography.body.copy(color = if (enabled) colors.content else colors.contentMuted),
            cursorBrush = SolidColor(colors.primary),
            keyboardOptions = keyboardOptions,
            keyboardActions = keyboardActions,
            visualTransformation = visualTransformation,
            modifier = Modifier
                .fillMaxWidth()
                .onFocusChanged { focused = it.isFocused },
            decorationBox = { innerTextField ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = spacing.touchTarget)
                        .clip(shape)
                        .background(if (enabled) colors.surface else colors.surfaceAccent.copy(alpha = colors.disabledAlpha))
                        .border(borderWidth, borderColor, shape)
                        .padding(start = spacing.md),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(spacing.xs),
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .padding(vertical = spacing.sm),
                        contentAlignment = Alignment.CenterStart,
                    ) {
                        if (value.isEmpty() && placeholder.isNotEmpty()) {
                            BasicText(
                                text = placeholder,
                                style = typography.body.copy(color = colors.contentMuted),
                            )
                        }
                        innerTextField()
                    }
                    trailing?.invoke()
                }
            },
        )
    }
}
