package id.kongstudio.cafe.feature.auth.session

import id.kongstudio.cafe.feature.access.Permission
import kotlinx.serialization.Serializable

@Serializable
data class LoginSession(
    val accessToken: String,
    val expiresInSeconds: Long,
    val user: UserProfile,
)

/** Profil staf yang masuk dari jawaban login; [permissions] hanya untuk menyembunyikan menu dan bukan pengamanan. */
@Serializable
data class UserProfile(
    val id: String,
    val name: String?,
    val username: String,
    /** Kosong bila akun tidak lagi memegang peran. */
    val roleId: String?,
    val roleName: String,
    val permissions: List<String>,
    /** Null berarti lintas cabang (pemilik). */
    val outletId: String?,
    val isActive: Boolean,
    val photoUrl: String?,
    /** Sifat peran dari server; peran berakses penuh datang dengan [permissions] kosong. */
    val hasFullAccess: Boolean,
) {
    /** Peran berakses penuh boleh semuanya dan peran lain hanya yang dicentang, hanya untuk menampilkan menu dan bukan pengamanan. */
    fun can(permission: Permission): Boolean = hasFullAccess || permission.key in permissions
}
