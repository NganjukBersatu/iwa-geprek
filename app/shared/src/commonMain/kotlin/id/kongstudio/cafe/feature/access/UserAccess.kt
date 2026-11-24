package id.kongstudio.cafe.feature.access

import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.admin.AdminApi
import id.kongstudio.cafe.feature.admin.AdminJson
import id.kongstudio.cafe.core.failure.isOffline
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.offline.userIdOf
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Kunci v2: salinan lama berbentuk backend lama dan tidak memuat penanda akses penuh.
private const val AccessCacheKey = "access.v2"

/** Identitas dan izin karyawan yang memegang tablet; yang menolak tetap server, ini hanya menentukan tampilan. */
internal class UserAccess(
    val userId: String,
    val name: String,
    val permissions: Set<String>,
    val fullAccess: Boolean = false,
) {
    fun allows(vararg wanted: Permission): Boolean = fullAccess || wanted.any { it.key in permissions }
}

@Serializable
private class MeDto(
    val id: String,
    val name: String? = null,
    val username: String = "",
    val permissions: List<String> = emptyList(),
    @SerialName("full_access") val fullAccess: Boolean = false,
)

/** Membaca izin dari server, dan dari salinan terakhir bila tablet sedang offline. */
internal class UserAccessRepository(
    private val api: AdminApi,
    private val store: OfflineStore,
    token: String,
) {
    private val userId = userIdOf(token)

    suspend fun load(): DeviceResult<UserAccess> {
        when (val result = api.get("/v2/auth/me", MeDto.serializer())) {
            is DeviceResult.Ok -> {
                userId?.let {
                    runCatching {
                        store.putCache(
                            "$it:$AccessCacheKey",
                            AdminJson.encodeToString(MeDto.serializer(), result.value),
                            ServerClock.nowEpochSeconds(),
                        )
                    }
                }
                return DeviceResult.Ok(result.value.toAccess())
            }
            is DeviceResult.Failed -> {
                if (!result.failure.isOffline) return result
                val cached = userId?.let { runCatching { store.getCache("$it:$AccessCacheKey") }.getOrNull() }
                    ?: return result
                return runCatching {
                    DeviceResult.Ok(AdminJson.decodeFromString(MeDto.serializer(), cached.body).toAccess())
                }.getOrElse { result }
            }
        }
    }

    private fun MeDto.toAccess() = UserAccess(id, name?.takeIf { it.isNotBlank() } ?: username, permissions.toSet(), fullAccess)
}
