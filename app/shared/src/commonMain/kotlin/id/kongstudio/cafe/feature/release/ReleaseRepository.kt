package id.kongstudio.cafe.feature.release

import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.map
import io.ktor.http.HttpMethod
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

private const val ReleaseReadPath = "/v2/operational/release-read"

@Serializable
internal class ReleaseReadDto(val version: String, val read: Boolean)

// Tanda baca ringkasan pembaruan milik karyawan yang memegang tablet.
internal class ReleaseRepository(private val api: AdminApi) {
    suspend fun read(version: String): DeviceResult<Boolean> =
        api.get(ReleaseReadPath, ReleaseReadDto.serializer(), mapOf("version" to version)).map { it.read }

    suspend fun markRead(version: String): DeviceResult<Unit> =
        api.sendUnit(HttpMethod.Patch, ReleaseReadPath, buildJsonObject { put("version", version) })
}
