package id.kongstudio.cafe.feature.update

import id.kongstudio.cafe.feature.admin.AdminJson
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.devicesetup.deviceCall
import io.ktor.client.HttpClient
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpMethod
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

private const val VersionPath = "/v2/client-version"
private val VersionPattern = Regex("""^(\d{1,4})\.(\d{1,4})\.(\d{1,4})$""")

/** Keadaan pembaruan wajib; [deferred] hanya berlaku selama sesi kasir di tablet ini masih berjalan. */
internal data class UpdateState(
    val required: Boolean = false,
    val minimum: String? = null,
    val downloadUrl: String? = null,
    val sessionOpen: Boolean = false,
    val deferred: Boolean = false,
) {
    val locked: Boolean get() = required && !(deferred && sessionOpen)
}

@Serializable
private class ClientVersionDto(
    @SerialName("apk_minimum") val apkMinimum: String? = null,
    @SerialName("download_url") val downloadUrl: String? = null,
)

/** Satu pintu pembaruan wajib di aplikasi: dibaca saat dibuka dan kembali ke layar, dan dikunci setiap server menolak versi ini (426). */
internal class AppUpdate(val installed: String) {
    private val _state = MutableStateFlow(UpdateState())
    val state: StateFlow<UpdateState> = _state.asStateFlow()

    /** Server menolak versi ini; versi minimum dan alamat unduhan dibaca lewat [check] sesudahnya. */
    fun refused() = _state.update { it.copy(required = true) }

    /** Gagal membaca tidak mengubah apa pun, jadi koneksi buruk tidak pernah mengunci atau membuka kunci. */
    suspend fun check(client: HttpClient, baseUrl: String) {
        val result = deviceCall(client, baseUrl, HttpMethod.Get, VersionPath) { response ->
            AdminJson.decodeFromString(ClientVersionDto.serializer(), response.bodyAsText())
        }
        val found = (result as? DeviceResult.Ok)?.value ?: return
        val minimum = found.apkMinimum
        val below = minimum != null && isBelow(installed, minimum)
        _state.update { it.copy(required = below, minimum = minimum, downloadUrl = found.downloadUrl) }
    }

    /** Dilaporkan layar kasir; kunci ditunda hanya selama sesi kasir berjalan, lalu berlaku begitu sesi ditutup. */
    fun sessionOpen(open: Boolean) = _state.update { it.copy(sessionOpen = open, deferred = it.deferred && open) }

    fun defer() = _state.update { if (it.sessionOpen) it.copy(deferred = true) else it }
}

private fun versionOf(text: String): Triple<Int, Int, Int>? =
    VersionPattern.matchEntire(text.trim())?.destructured?.let { (major, minor, patch) -> Triple(major.toInt(), minor.toInt(), patch.toInt()) }

/** Versi yang tidak terbaca tidak pernah mengunci siapa pun. */
internal fun isBelow(current: String, minimum: String): Boolean {
    val have = versionOf(current) ?: return false
    val need = versionOf(minimum) ?: return false
    return when {
        have.first != need.first -> have.first < need.first
        have.second != need.second -> have.second < need.second
        else -> have.third < need.third
    }
}
