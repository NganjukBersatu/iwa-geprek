package id.kongstudio.cafe.feature.profile

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.network.appendFile
import id.kongstudio.cafe.core.network.multipart
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

private const val PROFILE = "/v2/profile"

internal class KtorProfileRepository(private val api: ApiCaller) : ProfileRepository {

    override suspend fun load(): ApiResult<ProfileDetail> =
        api.read(PROFILE) { it.body<ProfileResponseDto>().toModel() }

    override suspend fun save(form: ProfileForm): WriteResult<ProfileDetail> =
        api.write(
            method = HttpMethod.Patch,
            path = PROFILE,
            configure = {
                contentType(ContentType.Application.Json)
                setBody(
                    ProfileUpdateDto(
                        name = form.name.trim(),
                        phone = form.phone.trim(),
                        address = form.address.trim(),
                        email = form.email.trim(),
                        gender = form.gender,
                        emergencyName = form.emergencyName.trim(),
                        emergencyPhone = form.emergencyPhone.trim(),
                        emergencyRelation = form.emergencyRelation.trim(),
                    ),
                )
            },
            parse = { it.body<ProfileResponseDto>().toModel() },
        )

    override suspend fun changePassword(oldPassword: String, newPassword: String): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = "$PROFILE/password",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(ChangePasswordDto(oldPassword, newPassword))
            },
            parse = { },
        )

    override suspend fun uploadPhoto(photo: ByteArray): WriteResult<ProfileDetail> =
        api.write(
            method = HttpMethod.Put,
            path = "$PROFILE/photo",
            configure = { multipart { appendFile("file", photo, "image/jpeg", "foto.jpg") } },
            parse = { it.body<ProfileResponseDto>().toModel() },
        )

    override suspend fun deletePhoto(): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Delete,
            path = "$PROFILE/photo",
            configure = {},
            parse = { },
        )
}
