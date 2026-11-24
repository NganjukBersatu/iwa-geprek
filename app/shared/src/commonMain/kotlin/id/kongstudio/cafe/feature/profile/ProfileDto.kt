package id.kongstudio.cafe.feature.profile

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class ProfileResponseDto(
    val name: String? = null,
    val username: String,
    @SerialName("role_name") val roleName: String,
    @SerialName("outlet_name") val outletName: String? = null,
    @SerialName("joined_date") val joinedDate: String? = null,
    @SerialName("birth_date") val birthDate: String? = null,
    val phone: String? = null,
    val address: String? = null,
    val email: String? = null,
    val gender: String? = null,
    @SerialName("emergency_name") val emergencyName: String? = null,
    @SerialName("emergency_phone") val emergencyPhone: String? = null,
    @SerialName("emergency_relation") val emergencyRelation: String? = null,
    @SerialName("photo_url") val photoUrl: String? = null,
) {
    fun toModel() = ProfileDetail(
        name = name?.takeIf { it.isNotBlank() } ?: username,
        username = username,
        roleName = roleName,
        outletName = outletName,
        joinedDate = joinedDate,
        birthDate = birthDate,
        phone = phone.orEmpty(),
        address = address.orEmpty(),
        email = email.orEmpty(),
        gender = gender,
        emergencyName = emergencyName.orEmpty(),
        emergencyPhone = emergencyPhone.orEmpty(),
        emergencyRelation = emergencyRelation.orEmpty(),
        photoUrl = photoUrl,
    )
}

/** Semua field dikirim agar kolom yang dikosongkan ikut terhapus di server. */
@Serializable
internal class ProfileUpdateDto(
    val name: String,
    val phone: String,
    val address: String,
    val email: String,
    val gender: String?,
    @SerialName("emergency_name") val emergencyName: String,
    @SerialName("emergency_phone") val emergencyPhone: String,
    @SerialName("emergency_relation") val emergencyRelation: String,
)

@Serializable
internal class ChangePasswordDto(
    @SerialName("current_password") val oldPassword: String,
    @SerialName("new_password") val newPassword: String,
)
