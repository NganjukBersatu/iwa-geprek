package id.kongstudio.cafe.feature.profile

import id.kongstudio.cafe.core.text.UiText

internal class ProfileDetail(
    val name: String,
    val username: String,
    val roleName: String,
    val outletName: String?,
    /** Tanggal "YYYY-MM-DD". */
    val joinedDate: String?,
    val birthDate: String?,
    val phone: String,
    val address: String,
    val email: String,
    /** "L" atau "P"; null bila belum diisi. */
    val gender: String?,
    val emergencyName: String,
    val emergencyPhone: String,
    val emergencyRelation: String,
    val photoUrl: String?,
)

/** Isian formulir data diri yang bisa diubah. */
internal data class ProfileForm(
    val name: String = "",
    val phone: String = "",
    val address: String = "",
    val email: String = "",
    val gender: String? = null,
    val emergencyName: String = "",
    val emergencyPhone: String = "",
    val emergencyRelation: String = "",
) {
    companion object {
        fun from(detail: ProfileDetail) = ProfileForm(
            name = detail.name,
            phone = detail.phone,
            address = detail.address,
            email = detail.email,
            gender = detail.gender,
            emergencyName = detail.emergencyName,
            emergencyPhone = detail.emergencyPhone,
            emergencyRelation = detail.emergencyRelation,
        )
    }
}

internal class FormMessage(val text: UiText, val success: Boolean)

internal const val MinPasswordLength = 6
