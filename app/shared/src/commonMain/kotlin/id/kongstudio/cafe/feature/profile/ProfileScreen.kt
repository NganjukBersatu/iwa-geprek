package id.kongstudio.cafe.feature.profile

import id.kongstudio.cafe.core.failure.AppFailure
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.nav_logout
import id.kongstudio.cafe.resources.password_confirm
import id.kongstudio.cafe.resources.password_hide
import id.kongstudio.cafe.resources.password_new
import id.kongstudio.cafe.resources.password_old
import id.kongstudio.cafe.resources.password_show
import id.kongstudio.cafe.resources.profile_account_joined
import id.kongstudio.cafe.resources.profile_account_outlet
import id.kongstudio.cafe.resources.profile_account_role
import id.kongstudio.cafe.resources.profile_account_username
import id.kongstudio.cafe.resources.profile_address
import id.kongstudio.cafe.resources.profile_birth_date
import id.kongstudio.cafe.resources.profile_change_password
import id.kongstudio.cafe.resources.profile_changing
import id.kongstudio.cafe.resources.profile_email
import id.kongstudio.cafe.resources.profile_emergency_name
import id.kongstudio.cafe.resources.profile_emergency_phone
import id.kongstudio.cafe.resources.profile_emergency_relation
import id.kongstudio.cafe.resources.profile_gender
import id.kongstudio.cafe.resources.profile_gender_female
import id.kongstudio.cafe.resources.profile_gender_male
import id.kongstudio.cafe.resources.profile_name
import id.kongstudio.cafe.resources.profile_phone
import id.kongstudio.cafe.resources.profile_photo_change
import id.kongstudio.cafe.resources.profile_photo_delete
import id.kongstudio.cafe.resources.profile_photo_delete_confirm
import id.kongstudio.cafe.resources.profile_photo_delete_message
import id.kongstudio.cafe.resources.profile_photo_delete_title
import id.kongstudio.cafe.resources.profile_photo_save
import id.kongstudio.cafe.resources.profile_photo_title
import id.kongstudio.cafe.resources.profile_save
import id.kongstudio.cafe.resources.profile_saving
import id.kongstudio.cafe.resources.profile_section_account
import id.kongstudio.cafe.resources.profile_section_password
import id.kongstudio.cafe.resources.profile_section_personal
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.choicegroup.ChoiceGroup
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.failurestate.FailureState
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.inlinemessage.MessageTone
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.loadingstate.LoadingState
import id.kongstudio.cafe.ui.component.passwordfield.PasswordField
import id.kongstudio.cafe.ui.component.photosubmitform.PhotoSubmitForm
import id.kongstudio.cafe.ui.component.secondarybutton.ButtonTone
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.sectiontitle.SectionTitle
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.component.profileheader.ProfileHeader
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val GenderMale = "L"
private const val GenderFemale = "P"

@Composable
internal fun ProfileScreen(
    state: ProfileUiState,
    fallbackName: String,
    fallbackRole: String,
    onFormChange: ((ProfileForm) -> ProfileForm) -> Unit,
    onSave: () -> Unit,
    onOldPasswordChange: (String) -> Unit,
    onNewPasswordChange: (String) -> Unit,
    onConfirmPasswordChange: (String) -> Unit,
    onChangePassword: () -> Unit,
    onUploadPhoto: (photo: ByteArray, onSuccess: () -> Unit) -> Unit,
    onClearPhotoError: () -> Unit,
    onDeletePhoto: (onSuccess: () -> Unit) -> Unit,
    onRetry: () -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val detail = state.detail
    var changingPhoto by remember { mutableStateOf(false) }
    var deletingPhoto by remember { mutableStateOf(false) }

    if (deletingPhoto) {
        ConfirmSheet(
            title = stringResource(Res.string.profile_photo_delete_title),
            message = state.photoError?.resolve() ?: stringResource(Res.string.profile_photo_delete_message),
            confirmLabel = stringResource(Res.string.profile_photo_delete_confirm),
            onConfirm = { onDeletePhoto { deletingPhoto = false } },
            onDismiss = {
                onClearPhotoError()
                deletingPhoto = false
            },
            destructive = true,
            enabled = !state.uploadingPhoto,
        )
    }

    if (changingPhoto) {
        AppBottomSheet(
            title = stringResource(Res.string.profile_photo_title),
            onDismiss = {
                onClearPhotoError()
                changingPhoto = false
            },
        ) {
            PhotoSubmitForm(
                submitLabel = stringResource(Res.string.profile_photo_save),
                onSubmit = { photo -> if (photo != null) onUploadPhoto(photo) { changingPhoto = false } },
                submitting = state.uploadingPhoto,
                error = state.photoError?.resolve(),
            )
            if (detail?.photoUrl != null) {
                SecondaryButton(
                    text = stringResource(Res.string.profile_photo_delete),
                    onClick = {
                        onClearPhotoError()
                        changingPhoto = false
                        deletingPhoto = true
                    },
                    tone = ButtonTone.Danger,
                    enabled = !state.uploadingPhoto,
                    modifier = Modifier.fillMaxWidth().padding(top = spacing.md),
                )
            }
        }
    }

    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        LazyColumn(
            modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxHeight(),
            contentPadding = PaddingValues(
                horizontal = AppTheme.windowSize.pagePadding,
                vertical = spacing.lg,
            ),
        ) {
            item {
                ProfileHeader(
                    name = detail?.name ?: fallbackName,
                    labels = listOfNotNull(detail?.roleName ?: fallbackRole, detail?.outletName),
                    photoUrl = detail?.photoUrl,
                    logoutLabel = stringResource(Res.string.nav_logout),
                    changePhotoLabel = stringResource(Res.string.profile_photo_change),
                    onLogout = onLogout,
                    onChangePhoto = if (detail != null) ({ changingPhoto = true }) else null,
                )
            }

            when {
                state.loading -> item { LoadingState() }

                state.failure != null || detail == null -> item { FailureState(failure = state.failure ?: AppFailure.Unexpected("Data kosong", "detail"), onRetry = onRetry) }

                else -> {
                    item { SectionTitle(stringResource(Res.string.profile_section_account)) }
                    item { AccountCard(detail) }

                    item { SectionTitle(stringResource(Res.string.profile_section_personal)) }
                    item { PersonalCard(state, onFormChange, onSave) }

                    item { SectionTitle(stringResource(Res.string.profile_section_password)) }
                    item {
                        PasswordCard(
                            state = state,
                            onOldChange = onOldPasswordChange,
                            onNewChange = onNewPasswordChange,
                            onConfirmChange = onConfirmPasswordChange,
                            onSubmit = onChangePassword,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun AccountCard(detail: ProfileDetail) {
    val none = "—"

    ListCard {
        DetailRow(stringResource(Res.string.profile_account_username), value = detail.username)
        AppDivider()
        DetailRow(stringResource(Res.string.profile_account_role), value = detail.roleName)
        AppDivider()
        DetailRow(stringResource(Res.string.profile_account_outlet), value = detail.outletName ?: none)
        AppDivider()
        DetailRow(
            stringResource(Res.string.profile_account_joined),
            value = detail.joinedDate?.let { longDateLabel(it) } ?: none,
        )
        AppDivider()
        DetailRow(
            stringResource(Res.string.profile_birth_date),
            value = detail.birthDate?.let { longDateLabel(it) } ?: none,
        )
    }
}

@Composable
private fun PersonalCard(
    state: ProfileUiState,
    onFormChange: ((ProfileForm) -> ProfileForm) -> Unit,
    onSave: () -> Unit,
) {
    val form = state.form
    val genders = listOf(GenderMale, GenderFemale)
    val enabled = !state.saving

    ListCard {
        Column(
            modifier = Modifier.fillMaxWidth().padding(AppTheme.spacing.md),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        ) {
            AppTextField(
                value = form.name,
                onValueChange = { v -> onFormChange { it.copy(name = v) } },
                label = stringResource(Res.string.profile_name),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
            )
            AppTextField(
                value = form.phone,
                onValueChange = { v -> onFormChange { it.copy(phone = v) } },
                label = stringResource(Res.string.profile_phone),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone, imeAction = ImeAction.Next),
            )
            AppTextField(
                value = form.email,
                onValueChange = { v -> onFormChange { it.copy(email = v) } },
                label = stringResource(Res.string.profile_email),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next),
            )
            AppTextField(
                value = form.address,
                onValueChange = { v -> onFormChange { it.copy(address = v) } },
                label = stringResource(Res.string.profile_address),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
            )
            ChoiceGroup(
                label = stringResource(Res.string.profile_gender),
                options = listOf(
                    stringResource(Res.string.profile_gender_male),
                    stringResource(Res.string.profile_gender_female),
                ),
                selectedIndex = genders.indexOf(form.gender).takeIf { it >= 0 },
                onSelect = { index -> onFormChange { it.copy(gender = genders[index]) } },
            )
            AppTextField(
                value = form.emergencyName,
                onValueChange = { v -> onFormChange { it.copy(emergencyName = v) } },
                label = stringResource(Res.string.profile_emergency_name),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
            )
            AppTextField(
                value = form.emergencyPhone,
                onValueChange = { v -> onFormChange { it.copy(emergencyPhone = v) } },
                label = stringResource(Res.string.profile_emergency_phone),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone, imeAction = ImeAction.Next),
            )
            AppTextField(
                value = form.emergencyRelation,
                onValueChange = { v -> onFormChange { it.copy(emergencyRelation = v) } },
                label = stringResource(Res.string.profile_emergency_relation),
                enabled = enabled,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            )
            state.saveMessage?.let { message ->
                InlineMessage(
                    text = message.text.resolve(),
                    tone = if (message.success) MessageTone.Success else MessageTone.Error,
                )
            }
            PrimaryButton(
                text = stringResource(if (state.saving) Res.string.profile_saving else Res.string.profile_save),
                onClick = onSave,
                enabled = enabled,
                loading = state.saving,
            )
        }
    }
}

@Composable
private fun PasswordCard(
    state: ProfileUiState,
    onOldChange: (String) -> Unit,
    onNewChange: (String) -> Unit,
    onConfirmChange: (String) -> Unit,
    onSubmit: () -> Unit,
) {
    val enabled = !state.changingPassword
    val show = stringResource(Res.string.password_show)
    val hide = stringResource(Res.string.password_hide)

    ListCard {
        Column(
            modifier = Modifier.fillMaxWidth().padding(AppTheme.spacing.md),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        ) {
            PasswordField(
                value = state.oldPassword,
                onValueChange = onOldChange,
                label = stringResource(Res.string.password_old),
                showDescription = show,
                hideDescription = hide,
                enabled = enabled,
                imeAction = ImeAction.Next,
            )
            PasswordField(
                value = state.newPassword,
                onValueChange = onNewChange,
                label = stringResource(Res.string.password_new),
                showDescription = show,
                hideDescription = hide,
                enabled = enabled,
                imeAction = ImeAction.Next,
            )
            PasswordField(
                value = state.confirmPassword,
                onValueChange = onConfirmChange,
                label = stringResource(Res.string.password_confirm),
                showDescription = show,
                hideDescription = hide,
                enabled = enabled,
                imeAction = ImeAction.Done,
                onImeAction = onSubmit,
            )
            state.passwordMessage?.let { message ->
                InlineMessage(
                    text = message.text.resolve(),
                    tone = if (message.success) MessageTone.Success else MessageTone.Error,
                )
            }
            PrimaryButton(
                text = stringResource(
                    if (state.changingPassword) Res.string.profile_changing else Res.string.profile_change_password,
                ),
                onClick = onSubmit,
                enabled = enabled && state.oldPassword.isNotEmpty(),
                loading = state.changingPassword,
            )
        }
    }
}
