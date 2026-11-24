package id.kongstudio.cafe.feature.auth.login

import id.kongstudio.cafe.feature.auth.session.LoginSession
import id.kongstudio.cafe.feature.auth.session.UserProfile
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal data class LoginRequestDto(
    val username: String,
    val password: String,
)

@Serializable
internal data class TokenResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("expires_in") val expiresIn: Long,
    val user: UserResponseDto,
) {
    fun toSession() = LoginSession(
        accessToken = accessToken,
        expiresInSeconds = expiresIn,
        user = user.toProfile(),
    )
}

@Serializable
internal data class UserResponseDto(
    val id: String,
    val name: String? = null,
    val username: String,
    @SerialName("role_id") val roleId: String? = null,
    @SerialName("role_name") val roleName: String,
    val permissions: List<String> = emptyList(),
    @SerialName("outlet_id") val outletId: String? = null,
    @SerialName("is_active") val isActive: Boolean,
    @SerialName("photo_url") val photoUrl: String? = null,
    @SerialName("full_access") val fullAccess: Boolean,
) {
    fun toProfile() = UserProfile(
        id = id,
        name = name,
        username = username,
        roleId = roleId,
        roleName = roleName,
        permissions = permissions,
        outletId = outletId,
        isActive = isActive,
        photoUrl = photoUrl,
        hasFullAccess = fullAccess,
    )
}
