package id.kongstudio.cafe.feature.profile

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface ProfileRepository {
    suspend fun load(): ApiResult<ProfileDetail>

    suspend fun save(form: ProfileForm): WriteResult<ProfileDetail>

    suspend fun changePassword(oldPassword: String, newPassword: String): WriteResult<Unit>

    /** Mengganti foto profil dengan JPEG [photo] dalam satu permintaan; mengembalikan profil terbaru. */
    suspend fun uploadPhoto(photo: ByteArray): WriteResult<ProfileDetail>

    suspend fun deletePhoto(): WriteResult<Unit>
}
