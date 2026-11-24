package id.kongstudio.cafe.ui.component.passwordfield

import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon

@Composable
fun PasswordField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    showDescription: String,
    hideDescription: String,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    enabled: Boolean = true,
    isError: Boolean = false,
    imeAction: ImeAction = ImeAction.Done,
    onImeAction: () -> Unit = {},
    labelColor: Color = AppTheme.colors.content,
    focusColor: Color = AppTheme.colors.primary,
) {
    var visible by remember { mutableStateOf(false) }
    val description = if (visible) hideDescription else showDescription

    AppTextField(
        value = value,
        onValueChange = onValueChange,
        label = label,
        modifier = modifier,
        placeholder = placeholder,
        enabled = enabled,
        isError = isError,
        labelColor = labelColor,
        focusColor = focusColor,
        visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = imeAction),
        keyboardActions = KeyboardActions(onDone = { onImeAction() }, onGo = { onImeAction() }),
        trailing = {
            Box(
                modifier = Modifier
                    .size(AppTheme.spacing.touchTarget)
                    .clip(AppTheme.shapes.pill)
                    .clickable(enabled = enabled, onClickLabel = description, role = Role.Button) {
                        visible = !visible
                    },
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(icon = if (visible) AppIcons.EyeOff else AppIcons.Eye, tint = AppTheme.colors.content, size = AppTheme.sizes.icon, contentDescription = description)
            }
        },
    )
}
