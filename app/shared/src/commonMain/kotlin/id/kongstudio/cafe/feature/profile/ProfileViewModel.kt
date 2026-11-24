package id.kongstudio.cafe.feature.profile

import id.kongstudio.cafe.core.failure.AppFailure
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.password_changed
import id.kongstudio.cafe.resources.password_mismatch
import id.kongstudio.cafe.resources.password_too_short
import id.kongstudio.cafe.resources.profile_name_required
import id.kongstudio.cafe.resources.profile_saved
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class ProfileUiState(
    val detail: ProfileDetail? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val form: ProfileForm = ProfileForm(),
    val saving: Boolean = false,
    val saveMessage: FormMessage? = null,
    val oldPassword: String = "",
    val newPassword: String = "",
    val confirmPassword: String = "",
    val changingPassword: Boolean = false,
    val passwordMessage: FormMessage? = null,
    val uploadingPhoto: Boolean = false,
    val photoError: UiText? = null,
)

internal class ProfileViewModel(
    private val repository: ProfileRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(ProfileUiState())
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    init {
        load()
    }

    fun load() {
        _state.update { it.copy(loading = true, failure = null) }
        viewModelScope.launch {
            when (val result = repository.load()) {
                is ApiResult.Success -> _state.update {
                    it.copy(
                        detail = result.value,
                        form = ProfileForm.from(result.value),
                        loading = false,
                    )
                }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    fun onFormChange(transform: (ProfileForm) -> ProfileForm) {
        _state.update { it.copy(form = transform(it.form), saveMessage = null) }
    }

    fun onOldPasswordChange(value: String) =
        _state.update { it.copy(oldPassword = value, passwordMessage = null) }

    fun onNewPasswordChange(value: String) =
        _state.update { it.copy(newPassword = value, passwordMessage = null) }

    fun onConfirmPasswordChange(value: String) =
        _state.update { it.copy(confirmPassword = value, passwordMessage = null) }

    fun save() {
        val current = _state.value
        if (current.saving) return
        if (current.form.name.isBlank()) {
            _state.update { it.copy(saveMessage = FormMessage(UiText.Resource(Res.string.profile_name_required), false)) }
            return
        }
        _state.update { it.copy(saving = true, saveMessage = null) }
        viewModelScope.launch {
            when (val result = repository.save(current.form)) {
                is WriteResult.Success -> _state.update {
                    it.copy(
                        detail = result.value,
                        form = ProfileForm.from(result.value),
                        saving = false,
                        saveMessage = FormMessage(UiText.Resource(Res.string.profile_saved), true),
                    )
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> finishSave(UiText.Failed(result.failure))
            }
        }
    }

    fun changePassword() {
        val current = _state.value
        if (current.changingPassword) return
        val problem = when {
            current.newPassword.length < MinPasswordLength -> Res.string.password_too_short
            current.newPassword != current.confirmPassword -> Res.string.password_mismatch
            else -> null
        }
        if (problem != null) {
            _state.update { it.copy(passwordMessage = FormMessage(UiText.Resource(problem), false)) }
            return
        }
        _state.update { it.copy(changingPassword = true, passwordMessage = null) }
        viewModelScope.launch {
            when (val result = repository.changePassword(current.oldPassword, current.newPassword)) {
                is WriteResult.Success -> _state.update {
                    it.copy(
                        changingPassword = false,
                        oldPassword = "",
                        newPassword = "",
                        confirmPassword = "",
                        passwordMessage = FormMessage(UiText.Resource(Res.string.password_changed), true),
                    )
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> finishPassword(UiText.Failed(result.failure))
            }
        }
    }

    /** Mengganti foto profil; [onSuccess] dipanggil setelah berhasil agar lembarnya menutup. */
    fun uploadPhoto(photo: ByteArray, onSuccess: () -> Unit) {
        if (_state.value.uploadingPhoto) return
        _state.update { it.copy(uploadingPhoto = true, photoError = null) }
        viewModelScope.launch {
            when (val result = repository.uploadPhoto(photo)) {
                is WriteResult.Success -> {
                    _state.update { it.copy(detail = result.value, uploadingPhoto = false) }
                    onSuccess()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> failPhoto(UiText.Failed(result.failure))
            }
        }
    }

    /** Menghapus foto profil lalu membaca ulang profil tanpa menimpa isian yang sedang diubah. */
    fun deletePhoto(onSuccess: () -> Unit) {
        if (_state.value.uploadingPhoto) return
        _state.update { it.copy(uploadingPhoto = true, photoError = null) }
        viewModelScope.launch {
            when (val result = repository.deletePhoto()) {
                is WriteResult.Success -> {
                    val fresh = (repository.load() as? ApiResult.Success)?.value
                    _state.update { it.copy(detail = fresh ?: it.detail, uploadingPhoto = false) }
                    onSuccess()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> failPhoto(UiText.Failed(result.failure))
            }
        }
    }

    fun clearPhotoError() = _state.update { it.copy(photoError = null) }

    private fun failPhoto(text: UiText) {
        _state.update { it.copy(uploadingPhoto = false, photoError = text) }
    }

    private fun rejectionText(message: String?, fallback: org.jetbrains.compose.resources.StringResource): UiText =
        message?.takeIf { it.isNotBlank() }?.let { UiText.Plain(it) } ?: UiText.Resource(fallback)

    private fun finishSave(text: UiText) {
        _state.update { it.copy(saving = false, saveMessage = FormMessage(text, false)) }
    }

    private fun finishPassword(text: UiText) {
        _state.update { it.copy(changingPassword = false, passwordMessage = FormMessage(text, false)) }
    }
}
