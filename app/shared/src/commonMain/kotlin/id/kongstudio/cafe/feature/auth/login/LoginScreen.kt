package id.kongstudio.cafe.feature.auth.login

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.login_brand_image
import id.kongstudio.cafe.resources.login_help
import id.kongstudio.cafe.resources.login_password_label
import id.kongstudio.cafe.resources.login_password_placeholder
import id.kongstudio.cafe.resources.login_submit
import id.kongstudio.cafe.resources.login_submitting
import id.kongstudio.cafe.resources.login_subtitle
import id.kongstudio.cafe.resources.login_title
import id.kongstudio.cafe.resources.login_username_label
import id.kongstudio.cafe.resources.login_username_placeholder
import id.kongstudio.cafe.resources.password_hide
import id.kongstudio.cafe.resources.password_show
import id.kongstudio.cafe.resources.brand_logo
import id.kongstudio.cafe.resources.shell_logo_description
import id.kongstudio.cafe.resources.storefront
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.authcard.AuthCard
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.passwordfield.PasswordField
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

private val LogoWidth = 44.dp
private val AccentBarWidth = 56.dp
private val AccentBarHeight = 3.dp

@Composable
fun LoginScreen(
    state: LoginUiState,
    onUsernameChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
    topAction: (@Composable () -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val hasError = state.error != null

    AuthCard(
        brandImage = painterResource(Res.drawable.storefront),
        brandDescription = stringResource(Res.string.login_brand_image),
        modifier = modifier,
        topAction = topAction,
    ) { wide ->
        Image(
            painter = painterResource(Res.drawable.brand_logo),
            contentDescription = stringResource(Res.string.shell_logo_description),
            contentScale = ContentScale.FillWidth,
            modifier = Modifier.width(LogoWidth),
        )
        Spacer(Modifier.height(spacing.lg))
        AppText(
            text = stringResource(Res.string.login_title),
            role = if (wide) TextRole.Headline else TextRole.Title,
            color = colors.content,
        )
        Spacer(Modifier.height(spacing.sm))
        Box(
            modifier = Modifier
                .width(AccentBarWidth)
                .height(AccentBarHeight)
                .clip(AppTheme.shapes.pill)
                .background(colors.primary),
        )
        Spacer(Modifier.height(spacing.md))
        AppText(
            text = stringResource(Res.string.login_subtitle),
            role = TextRole.Caption,
            color = colors.contentMuted,
        )
        Spacer(Modifier.height(if (wide) spacing.xl else spacing.lg))

        AppTextField(
            value = state.username,
            onValueChange = onUsernameChange,
            label = stringResource(Res.string.login_username_label),
            placeholder = stringResource(Res.string.login_username_placeholder),
            enabled = !state.submitting,
            isError = hasError,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Text,
                imeAction = ImeAction.Next,
            ),
        )
        Spacer(Modifier.height(spacing.lg))

        PasswordField(
            value = state.password,
            onValueChange = onPasswordChange,
            label = stringResource(Res.string.login_password_label),
            placeholder = stringResource(Res.string.login_password_placeholder),
            showDescription = stringResource(Res.string.password_show),
            hideDescription = stringResource(Res.string.password_hide),
            enabled = !state.submitting,
            isError = hasError,
            onImeAction = { if (state.canSubmit) onSubmit() },
        )

        state.error?.let { error ->
            Spacer(Modifier.height(spacing.md))
            InlineMessage(text = error.resolve())
        }

        Spacer(Modifier.height(if (wide) spacing.xl else spacing.lg))
        PrimaryButton(
            text = stringResource(if (state.submitting) Res.string.login_submitting else Res.string.login_submit),
            onClick = onSubmit,
            enabled = state.canSubmit,
            loading = state.submitting,
        )

        Spacer(Modifier.height(spacing.lg))
        AppText(
            text = stringResource(Res.string.login_help),
            role = TextRole.Caption,
            color = colors.contentMuted,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
